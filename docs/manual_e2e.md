# 真实 DeepSeek E2E 验收记录

- 验收日期：2026-08-21
- Provider：DeepSeek OpenAI-compatible API
- 模型：`deepseek-v4-flash`
- Base URL：`https://api.deepseek.com`
- API Key：已通过本地 `.env` 配置，本文档不记录具体值
- 验收方式：用户按照 README 的真实 Provider 流程手动执行

## 验收结果

| 场景 | 结果 | 工具执行 | 核心观察 |
| --- | --- | --- | --- |
| 普通聊天 | 通过 | 无 | Provider 正常返回文本 |
| 查询 `active_users` | 通过 | `lookup_metric` | 返回本地指标数据 |
| 查询 `TASK-1001` | 通过 | `query_status` | 返回任务状态与进度 |
| 创建结构化摘要 | 通过 | `create_summary` | 返回确定性摘要结果 |
| 缺参跨轮补齐 | 通过 | 第二轮执行 | 第一轮追问，补充参数后执行 |
| 查询不存在的指标 | 通过 | `lookup_metric` | `not_found` 被转换为明确回答 |
| 未知或越权工具请求 | 通过 | 未执行 | 白名单边界有效 |
| 查看与重置会话 | 通过 | 无 | `/state` 与 `/reset` 工作正常 |
| 极简 Web 页面 | 通过 | 按请求执行 | 聊天、步骤、状态与重置可用 |
| Provider 错误提示 | 通过 | 未执行或中止 | 认证、超时和异常有明确提示 |

## 自动化回归

真实 Provider 验收之外，仓库还使用 Fake model 运行确定性 E2E，覆盖成功调用、
缺参跨轮补齐、未知工具回滚、非法参数、业务失败和 Provider 超时等场景。

```bash
python -m pytest tests/test_dialogues.py -q
python -m pytest -q
```

真实 API 验收不加入默认 pytest，避免测试结果受网络、模型随机性和账户额度影响。
