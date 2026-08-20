"""零额外依赖的本地任务 Agent Web 页面。"""

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

from app.agent import (
    AgentRunner,
    OpenAICompatibleAgentModel,
)
from app.config import load_settings
from app.errors import (
    AppError,
    ConfigurationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    UserInputError,
)
from app.execution import ToolRouter
from app.llm_client import create_client
from app.logging_config import configure_logging
from app.session import ConversationSession
from app.tools.models import JSONValue


logger = logging.getLogger(__name__)

STATIC_ROOT = Path(__file__).with_name("static")
MAX_REQUEST_BYTES = 64 * 1024


class WebApplication:
    """把 HTTP payload 转换成会话操作。"""

    def __init__(
        self,
        session: ConversationSession,
    ) -> None:
        self._session = session

    def chat(
        self,
        payload: object,
    ) -> dict[str, JSONValue]:
        """处理一条网页聊天消息。"""

        if not isinstance(payload, dict):
            raise UserInputError(
                "请求体必须是 JSON object。"
            )

        message = payload.get("message")
        if not isinstance(message, str):
            raise UserInputError(
                "message 必须是字符串。"
            )

        result = self._session.send(message)
        return {
            "answer": result.answer,
            "finish_reason": result.finish_reason,
            "model_rounds": result.model_rounds,
            "tool_steps": [
                step.to_dict()
                for step in result.tool_steps
            ],
            "state": self._session.state.to_dict(),
        }

    def state(self) -> dict[str, JSONValue]:
        """返回当前短期会话状态。"""

        return self._session.state.to_dict()

    def reset(self) -> dict[str, JSONValue]:
        """重置并返回新的会话状态。"""

        return self._session.reset().to_dict()


class TaskAgentRequestHandler(
    BaseHTTPRequestHandler
):
    """本地静态页面和 JSON API handler。"""

    application: WebApplication

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/api/state":
            self._send_json(
                200,
                self.application.state(),
            )
            return

        static_files = {
            "/": (
                "index.html",
                "text/html; charset=utf-8",
            ),
            "/static/styles.css": (
                "styles.css",
                "text/css; charset=utf-8",
            ),
            "/static/app.js": (
                "app.js",
                "text/javascript; charset=utf-8",
            ),
        }
        static_file = static_files.get(path)
        if static_file is None:
            self._send_json(
                404,
                {"error": "页面不存在。"},
            )
            return

        filename, content_type = static_file
        file_path = STATIC_ROOT / filename

        try:
            content = file_path.read_bytes()
        except OSError:
            logger.exception(
                "读取静态文件失败：%s",
                file_path,
            )
            self._send_json(
                500,
                {"error": "静态页面读取失败。"},
            )
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header(
            "Content-Length",
            str(len(content)),
        )
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        path = urlparse(self.path).path

        try:
            if path == "/api/chat":
                payload = self._read_json()
                self._send_json(
                    200,
                    self.application.chat(payload),
                )
                return

            if path == "/api/reset":
                self._send_json(
                    200,
                    self.application.reset(),
                )
                return

            self._send_json(
                404,
                {"error": "API 路径不存在。"},
            )
        except UserInputError as exc:
            self._send_json(
                400,
                {"error": str(exc)},
            )
        except ProviderRateLimitError as exc:
            self._send_json(
                429,
                {"error": str(exc)},
            )
        except ProviderTimeoutError as exc:
            self._send_json(
                504,
                {"error": str(exc)},
            )
        except AppError as exc:
            self._send_json(
                500,
                {"error": str(exc)},
            )
        except Exception:
            logger.exception(
                "Web API 未处理异常"
            )
            self._send_json(
                500,
                {"error": "服务器发生未预期异常。"},
            )

    def _read_json(self) -> object:
        raw_length = self.headers.get(
            "Content-Length"
        )
        if raw_length is None:
            raise UserInputError(
                "请求缺少 Content-Length。"
            )

        try:
            length = int(raw_length)
        except ValueError as exc:
            raise UserInputError(
                "Content-Length 无效。"
            ) from exc

        if length <= 0:
            raise UserInputError(
                "请求体不能为空。"
            )

        if length > MAX_REQUEST_BYTES:
            raise UserInputError(
                "请求体不能超过 64 KiB。"
            )

        raw_body = self.rfile.read(length)
        try:
            return json.loads(
                raw_body.decode("utf-8")
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise UserInputError(
                "请求体必须是 UTF-8 JSON。"
            ) from exc

    def _send_json(
        self,
        status: int,
        payload: dict[str, JSONValue],
    ) -> None:
        content = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )
        self.send_header(
            "Content-Length",
            str(len(content)),
        )
        self.end_headers()
        self.wfile.write(content)

    def log_message(
        self,
        format: str,
        *args: object,
    ) -> None:
        logger.info(
            "%s - %s",
            self.client_address[0],
            format % args,
        )


def build_server(
    application: WebApplication,
    host: str,
    port: int,
) -> ThreadingHTTPServer:
    """创建绑定当前 WebApplication 的服务器。"""

    class BoundRequestHandler(
        TaskAgentRequestHandler
    ):
        pass

    BoundRequestHandler.application = application
    return ThreadingHTTPServer(
        (host, port),
        BoundRequestHandler,
    )


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="local-task-agent-web",
        description="本地任务 Agent 极简页面",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="监听地址，默认仅本机可访问。",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="监听端口，默认 8000。",
    )
    parser.add_argument(
        "--session-id",
        default="web-local",
        help="网页使用的本地会话标识。",
    )
    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = parse_args(argv)

    try:
        if not 1 <= args.port <= 65535:
            raise ValueError(
                "port 必须在 1 到 65535 之间。"
            )

        settings = load_settings()
        configure_logging(settings.log_level)

        client = create_client(settings)
        model = OpenAICompatibleAgentModel(
            client=client,
            model=settings.model,
        )
        runner = AgentRunner(
            model=model,
            router=ToolRouter(),
        )
        session = ConversationSession(
            runner=runner,
            session_id=args.session_id,
        )
        application = WebApplication(session)
        server = build_server(
            application=application,
            host=args.host,
            port=args.port,
        )

        print(
            "本地页面已启动："
            f"http://{args.host}:{args.port}"
        )
        print("按 Ctrl+C 停止。")

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n已停止。")
        finally:
            server.server_close()

        return 0
    except (ConfigurationError, ValueError) as exc:
        print(
            f"启动失败：{exc}",
            file=sys.stderr,
        )
        return 2
    except OSError as exc:
        print(
            f"无法启动本地服务器：{exc}",
            file=sys.stderr,
        )
        return 1
    except Exception:
        logger.exception("Web 服务启动失败")
        print(
            "Web 服务启动失败，请查看日志。",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
