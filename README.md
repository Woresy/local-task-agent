# Local Task Agent

本地运行的任务型 AI 聊天机器人。

当前为阶段 1，只包含：

- DeepSeek OpenAI-compatible SDK 配置
- system prompt 与 messages
- 单轮普通聊天 CLI
- 超时、认证、限流和异常响应处理
- 基础单元测试

当前尚未接入工具和 Agent loop。

## 环境要求

- Python 3.10+
- DeepSeek API Key

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 配置

```bash
cp .env.example .env
```

编辑 `.env`：

```dotenv
DEEPSEEK_API_KEY=你的真实API-Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
REQUEST_TIMEOUT=30
MAX_RETRIES=2
LOG_LEVEL=INFO
```

`.env` 已加入 `.gitignore`，不得提交真实 API Key。

## 运行

直接提供消息：

```bash
python -m app.main --message "请用一句话介绍你自己"
```

从终端输入：

```bash
python -m app.main
```

## 测试

```bash
python -m compileall -q app tests
python -m pytest -q
```

## CLI 退出码

- `0`：调用成功
- `1`：Provider 或程序异常
- `2`：配置或用户输入错误
- `130`：用户取消