"""单进程内的短期多轮会话。"""

from app.agent.models import AgentRunResult
from app.agent.prompts import (
    build_agent_system_message,
    build_agent_user_message,
)
from app.agent.runner import AgentRunner
from app.session.models import SessionState


class ConversationSession:
    """保存 messages 并协调多轮 Agent 调用。"""

    def __init__(
        self,
        runner: AgentRunner,
        session_id: str = "local",
    ) -> None:
        normalized_id = session_id.strip()

        if not normalized_id:
            raise ValueError(
                "session_id 不能为空。"
            )

        self._runner = runner
        self._state = SessionState(
            session_id=normalized_id,
            messages=(
                build_agent_system_message(),
            ),
        )

    @property
    def state(self) -> SessionState:
        """返回当前不可变状态快照。"""

        return self._state

    def send(
        self,
        user_text: str,
    ) -> AgentRunResult:
        """提交一条用户消息并在成功后更新状态。"""

        candidate_messages = (
            *self._state.messages,
            build_agent_user_message(user_text),
        )
        outcome = self._runner.run_messages(
            candidate_messages
        )
        new_state = SessionState(
            session_id=self._state.session_id,
            messages=outcome.messages,
            turn_count=self._state.turn_count + 1,
            last_finish_reason=(
                outcome.result.finish_reason
            ),
        )
        self._state = new_state
        return outcome.result

    def reset(self) -> SessionState:
        """清空历史并保留 session_id。"""

        self._state = SessionState(
            session_id=self._state.session_id,
            messages=(
                build_agent_system_message(),
            ),
        )
        return self._state
