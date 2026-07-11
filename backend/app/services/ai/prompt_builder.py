from __future__ import annotations

import json
from typing import Any


def build_grounded_prompt(question: str, evidence: dict[str, Any]) -> str:
    compact = json.dumps(evidence, ensure_ascii=False, default=str)
    return (
        "請根據下列 JSON evidence 回答使用者問題。"
        "只能引用 evidence 中存在的資料；資料不足時要明確說明。"
        "回答焦點限於訓練、恢復、負荷與日常查詢，不提供醫療診斷。\n\n"
        f"Question:\n{question}\n\n"
        f"Evidence JSON:\n{compact}"
    )

