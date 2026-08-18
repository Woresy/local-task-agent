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

## 阶段 5：安全工具路由与单次执行

阶段 5 通过静态 `TOOL_REGISTRY` 白名单执行本地工具。

执行前必须满足：

- 参数校验状态为 `ready`
- 工具名称存在于白名单
- 工具返回统一的 `ToolResult`
- 返回结果中的工具名称与请求一致

未知工具、缺参和非法参数不会执行。

### 单次执行工具

```bash
python -m app.execution_cli \
  --tool lookup_metric \
  --arguments '{"name":"active_users"}'
```

## 阶段 6：真实 Agent tool loop

阶段 6 使用 OpenAI-compatible Chat Completions `tools`：

1. 模型返回普通文本或 `tool_calls`
2. 程序解析 function arguments
3. 使用阶段 4 校验参数
4. 使用阶段 5 白名单执行工具
5. 将 `ToolResult` 作为 `tool message` 回传模型
6. 模型生成最终回答

每次运行最多允许 4 轮模型请求，防止无限工具循环。

### 运行一次 Agent

```bash
python -m app.agent_cli \
  --message "查询 active_users" \
  --show-steps
```

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
