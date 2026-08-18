"""真实 tool calling Agent 的有限循环。"""

from typing import cast

from openai.types.chat import (
    ChatCompletionMessageParam,
)

from app.agent.messages import (
    build_assistant_message,
    build_tool_result_message,
)
from app.agent.model import AgentModel
from app.agent.models import (
    AgentRunResult,
    AgentToolStep,
)
from app.agent.parsing import (
    parse_tool_arguments,
)
from app.agent.prompts import (
    build_agent_messages,
)
from app.errors import (
    AgentLoopLimitError,
    AgentProtocolError,
)
from app.execution import ToolRouter
from app.tools.models import ToolName
from app.validation import (
    build_follow_up_question,
    validate_tool_arguments,
)


class AgentRunner:
    """协调模型、参数校验器和工具 Router。"""

    def __init__(
        self,
        model: AgentModel,
        router: ToolRouter,
        max_model_rounds: int = 4,
    ) -> None:
        if max_model_rounds <= 0:
            raise ValueError(
                "max_model_rounds 必须大于 0。"
            )

        self._model = model
        self._router = router
        self._max_model_rounds = (
            max_model_rounds
        )

    def run(
        self,
        user_text: str,
    ) -> AgentRunResult:
        """完成一次用户输入对应的 Agent 运行。"""

        messages: list[
            ChatCompletionMessageParam
        ] = build_agent_messages(user_text)

        tool_steps: list[AgentToolStep] = []
        model_rounds = 0

        while (
            model_rounds
            < self._max_model_rounds
        ):
            reply = self._model.complete(messages)
            model_rounds += 1

            if not reply.tool_calls:
                if reply.content is None:
                    raise AgentProtocolError(
                        "Agent 模型未返回最终文本。"
                    )

                return AgentRunResult(
                    answer=reply.content,
                    finish_reason="completed",
                    model_rounds=model_rounds,
                    tool_steps=tuple(tool_steps),
                )

            if len(reply.tool_calls) != 1:
                raise AgentProtocolError(
                    "一次模型响应只能请求一个工具。"
                )

            tool_call = reply.tool_calls[0]
            self._router.resolve_tool(tool_call.name)
            tool_name = cast(ToolName, tool_call.name)
            arguments = parse_tool_arguments(
                tool_call.arguments_json
            )
            validation = validate_tool_arguments(
                tool_name,
                arguments,
            )

            if validation.status == "needs_clarification":
                question = build_follow_up_question(
                    validation
                )
                if question is None:
                    raise AgentProtocolError(
                        "工具缺参时未生成追问文本。"
                    )

                return AgentRunResult(
                    answer=question,
                    finish_reason="needs_clarification",
                    model_rounds=model_rounds,
                    tool_steps=tuple(tool_steps),
                )

            if validation.status == "invalid":
                return AgentRunResult(
                    answer="\n".join(
                        issue.message
                        for issue in validation.issues
                    ),
                    finish_reason="invalid_arguments",
                    model_rounds=model_rounds,
                    tool_steps=tuple(tool_steps),
                )

            result = self._router.execute(validation)
            tool_steps.append(
                AgentToolStep(
                    call_id=tool_call.call_id,
                    tool_name=tool_name,
                    arguments=(
                        validation.validated_arguments
                    ),
                    result=result,
                )
            )
            messages.append(
                build_assistant_message(reply)
            )
            messages.append(
                build_tool_result_message(
                    tool_call.call_id,
                    result,
                )
            )

        raise AgentLoopLimitError(
            "Agent 达到最大模型轮数，"
            "仍未产生最终回答。"
        )
