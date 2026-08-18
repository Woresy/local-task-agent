"""应用层异常类型。"""


class AppError(Exception):
    """可以转换为明确 CLI 提示的应用异常。"""


class ConfigurationError(AppError):
    """环境变量或 Provider 配置错误。"""


class UserInputError(AppError):
    """用户输入不符合当前 CLI 要求。"""


class ProviderError(AppError):
    """模型 Provider 调用失败。"""


class ProviderAuthenticationError(ProviderError):
    """API Key 无效或无权访问模型。"""


class ProviderTimeoutError(ProviderError):
    """模型请求超时。"""


class ProviderRateLimitError(ProviderError):
    """模型服务触发限流或账户额度不足。"""


class ProviderConnectionError(ProviderError):
    """无法连接模型 Provider。"""


class ProviderResponseError(ProviderError):
    """Provider 返回错误状态或非预期响应。"""

class ToolExecutionError(AppError):
    """工具执行过程中出现非预期异常。"""

class IntentRecognitionError(AppError):
    """意图识别结果为空、格式错误或违反协议。"""

class ArgumentValidationError(AppError):
    """参数校验器收到无法处理的输入或配置。"""

class UnknownToolError(ToolExecutionError):
    """请求的工具不在允许执行的注册表中。"""


class ToolNotReadyError(ToolExecutionError):
    """工具参数尚未达到可执行状态。"""


class ToolContractError(ToolExecutionError):
    """工具返回值违反统一 ToolResult 契约。"""