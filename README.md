# Local Task Agent

本地运行的任务型 AI 聊天机器人。

## 阶段 1，只包含：

- DeepSeek OpenAI-compatible SDK 配置
- system prompt 与 messages
- 单轮普通聊天 CLI
- 超时、认证、限流和异常响应处理
- 基础单元测试


## 阶段 2：本地工具

当前提供三个可独立执行的本地工具：

- `lookup_metric(name)`：查询业务指标
- `query_status(id)`：查询任务状态
- `create_summary(data)`：生成确定性的结构化摘要

工具当前使用本地演示数据，不依赖模型执行。

### 直接运行工具

```bash
python -c "from app.tools import lookup_metric; print(lookup_metric('active_users').to_json())"
```

```bash
python -c "from app.tools import query_status; print(query_status('TASK-1001').to_json())"
```

```bash
python -c "from app.tools import create_summary; print(create_summary({'stage': 2}).to_json())"
```

## 阶段 3：结构化意图识别

当前支持把用户文本识别为以下意图：

- `lookup_metric`
- `query_status`
- `create_summary`
- `general_chat`
- `unknown`

识别结果包含：

- `intent`
- `arguments`
- `confidence`
- `reason`

参数允许不完整；当前尚未执行缺参追问或工具路由。

### 查看意图识别结果

```bash
python -m app.intent_cli --message "查询 active_users"
```

示例输出：

```json
{
  "intent": "lookup_metric",
  "arguments": {
    "name": "active_users"
  },
  "confidence": 0.95,
  "reason": "用户明确查询业务指标"
}
```
## 阶段 4：参数校验与缺参追问

阶段 4 在执行工具前检查结构化 arguments，支持三种结果：

- `ready`：参数完整，可以进入工具路由
- `needs_clarification`：缺少必填参数，需要追问用户
- `invalid`：参数类型错误或包含未定义字段

当前阶段只校验参数并生成追问，不执行工具，不更新会话状态。

### 查看参数校验结果

```bash
python -m app.validation_cli \
  --tool query_status \
  --arguments '{}'
```

## 阶段 5：工具选择、安全路由与 Agent 工具循环

阶段 5 先通过静态 `TOOL_REGISTRY` 白名单安全执行本地工具，
再使用 OpenAI-compatible Chat Completions `tools` 形成真实 Agent tool loop。

### 5.1 安全工具路由与单次执行

执行前必须满足：

- 参数校验状态为 `ready`
- 工具名称存在于白名单
- 工具返回统一的 `ToolResult`
- 返回结果中的工具名称与请求一致

未知工具、缺参和非法参数不会执行。

#### 单次执行工具

```bash
python -m app.execution_cli \
  --tool lookup_metric \
  --arguments '{"name":"active_users"}'
```

### 5.2 真实 Agent tool loop

Agent 使用 OpenAI-compatible Chat Completions `tools`：

1. 模型返回普通文本或 `tool_calls`
2. 程序解析 function arguments
3. 使用阶段 4 校验参数
4. 使用阶段 5 白名单执行工具
5. 将 `ToolResult` 作为 `tool message` 回传模型
6. 模型生成最终回答

每次运行最多允许 4 轮模型请求，防止无限工具循环。

#### 运行一次 Agent

```bash
python -m app.agent_cli \
  --message "查询 active_users" \
  --show-steps
```

## 阶段 6：多轮 CLI 与系统错误处理

阶段 6 使用 `ConversationSession` 在当前进程内保存短期会话状态，
包括完整 Chat Completions messages、对话轮数和上一轮结束原因。

当前支持：

- 连续多轮对话，并把历史 messages 传给下一轮模型请求
- 工具缺参后跨轮补齐参数
- 使用 `/state` 查看当前会话状态
- 使用 `/reset` 清空历史并保留 session ID
- 使用 `/exit` 或 `/help` 退出或查看命令
- 模型超时、限流或工具异常时保留上一份有效状态
- 可选显示本轮真实工具执行步骤

会话采用事务式更新：先基于旧状态运行完整 Agent 回合，成功后才提交新的
`SessionState`。如果 Provider 或工具执行失败，本轮 user message 不会写入状态。

### 运行多轮 CLI

```bash
python -m app.chat_cli --show-steps
```

指定本地会话标识：

```bash
python -m app.chat_cli \
  --session-id demo-session \
  --show-steps
```

### 跨轮补齐参数

```text
你：帮我查询任务状态
助手：请提供要查询的任务 ID，例如 TASK-1001。
你：TASK-1001
助手：TASK-1001 正在运行，当前进度为 65%。
```

### 会话命令

- `/state`：显示 session ID、轮数、messages 和是否等待补参
- `/reset`：清除当前会话历史，只保留 system message
- `/help`：显示可用命令
- `/exit`：正常退出 CLI

短期状态只保存在当前 Python 进程内，关闭程序后不会持久化到磁盘。

## 阶段 7：E2E 验收、极简页面与项目交付

阶段 7 使用可重复的 Fake model 响应驱动完整应用链路，同时调用真实本地工具。
测试不会消耗 Provider API 额度，也不会依赖模型输出的随机性。

当前提供 13 条独立 E2E 对话测试，覆盖：

1. 普通问候不调用工具
2. 成功查询业务指标
3. 成功查询任务状态
4. 成功创建结构化摘要
5. 工具返回 `not_found` 后由模型解释结果
6. 缺少任务 ID 后跨轮补齐
7. 缺少指标名称后跨轮补齐
8. 缺少摘要数据后跨轮补齐
9. 参数类型错误时不执行工具
10. 未知工具失败且会话状态回滚
11. 范围外请求明确拒绝
12. Provider 超时时会话状态回滚
13. 同一响应包含多个 tool calls 时拒绝执行并回滚

### E2E 对话测试

```bash
python -m pytest tests/test_dialogues.py -q
```

预期结果：

```text
13 passed
```

### 极简本地页面

页面和 JSON API 使用 Python 标准库实现，不需要安装额外 Web framework。
服务默认只监听 `127.0.0.1`，复用与多轮 CLI 相同的 `ConversationSession`。

```bash
python -m app.web
```

浏览器访问：<http://127.0.0.1:8000>

可选参数：

```bash
python -m app.web \
  --host 127.0.0.1 \
  --port 8000 \
  --session-id web-local
```

页面支持连续聊天、显示真实工具步骤、查看状态和重置会话。关闭 Python
进程后，页面的短期会话状态会丢失。

### 验收矩阵

| 验收项 | 实现与证据 |
| --- | --- |
| 本地连续多轮对话 | `app.chat_cli`、Web 页面与 `ConversationSession` |
| 至少 3 类意图 | 5 类结构化意图与 3 类工具意图 |
| 至少 2 个真实工具 | `lookup_metric`、`query_status`、`create_summary` |
| 多轮补齐缺失参数 | 3 个跨轮补齐 E2E 场景 |
| 未知工具不执行 | 未知工具回滚 E2E 与 Router 单元测试 |
| 短期状态可查看 | CLI `/state`、页面状态面板与 `SessionState.to_json()` |
| API Key 不入库 | `.env` 已忽略，只提交 `.env.example` |
| Provider 错误提示 | 缺密钥、认证、超时、限流、连接和异常响应映射 |
| 不少于 5 个单元测试 | 完整 pytest 测试套件 |
| 不少于 10 个对话测试 | `tests/test_dialogues.py` 中 13 条 E2E |

### 真实 Provider 手动验收

自动化 E2E 使用 Fake model 保证稳定性；发布前仍应使用 `.env` 中的真实配置运行：

```bash
python -m app.chat_cli --show-steps
```

依次验证普通聊天、指标查询、任务查询、摘要生成和缺参跨轮补齐，确认 Provider
能够真实返回 `tool_calls`，并且 CLI 显示真实工具执行步骤。

本项目已于 2026-08-21 使用 `deepseek-v4-flash` 完成真实 API 手动验收。
详细记录见 [`docs/manual_e2e.md`](docs/manual_e2e.md)。

GitHub 仓库：<https://github.com/Woresy/local-task-agent>

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

推荐运行支持工具调用和短期状态的多轮 CLI：

```bash
python -m app.chat_cli --show-steps
```

运行极简本地页面：

```bash
python -m app.web
```

浏览器访问：<http://127.0.0.1:8000>

运行一次真实 tool calling Agent：

```bash
python -m app.agent_cli \
  --message "查询 active_users" \
  --show-steps
```

阶段 1 的普通单轮聊天入口仍可使用：

```bash
python -m app.main --message "请用一句话介绍你自己"
```

## 测试

运行 13 条 E2E 对话测试：

```bash
python -m pytest tests/test_dialogues.py -q
```

运行完整测试：

```bash
python -m compileall -q app tests
python -m pytest -q
```

当前自动化测试结果：

```text
134 passed
```

## CLI 退出码

- `0`：调用成功
- `1`：Provider 或程序异常
- `2`：配置或用户输入错误
- `130`：用户取消
