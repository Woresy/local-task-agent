"""阶段 2 使用的确定性本地演示数据。"""

from app.tools.models import JSONValue


METRIC_STORE: dict[
    str,
    dict[str, JSONValue],
] = {
    "active_users": {
        "name": "active_users",
        "value": 1280,
        "unit": "users",
        "updated_at": "2026-08-18T09:00:00+08:00",
        "source": "local_demo_store",
    },
    "conversion_rate": {
        "name": "conversion_rate",
        "value": 0.184,
        "unit": "ratio",
        "updated_at": "2026-08-18T09:00:00+08:00",
        "source": "local_demo_store",
    },
    "avg_response_ms": {
        "name": "avg_response_ms",
        "value": 236,
        "unit": "ms",
        "updated_at": "2026-08-18T09:00:00+08:00",
        "source": "local_demo_store",
    },
}


STATUS_STORE: dict[
    str,
    dict[str, JSONValue],
] = {
    "TASK-1001": {
        "id": "TASK-1001",
        "status": "running",
        "progress": 65,
        "updated_at": "2026-08-18T09:05:00+08:00",
        "source": "local_demo_store",
    },
    "TASK-1002": {
        "id": "TASK-1002",
        "status": "completed",
        "progress": 100,
        "updated_at": "2026-08-18T08:30:00+08:00",
        "source": "local_demo_store",
    },
    "TASK-1003": {
        "id": "TASK-1003",
        "status": "failed",
        "progress": 42,
        "updated_at": "2026-08-18T08:45:00+08:00",
        "source": "local_demo_store",
    },
}