from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    model_name: str

    @abstractmethod
    def generate(self, prompt: str, evidence: dict[str, Any]) -> str:
        """Generate a grounded answer from provided evidence only."""


class LocalEvidenceProvider(AIProvider):
    model_name = "local-rule-based"

    def generate(self, prompt: str, evidence: dict[str, Any]) -> str:
        if not evidence.get("has_data"):
            return "資料不足：目前資料庫沒有足夠的 Garmin 活動或健康資料，無法做訓練與恢復分析。"

        latest_health = evidence.get("latest_health") or {}
        latest_metric = evidence.get("latest_metric") or {}
        activities = evidence.get("activities") or []
        risk = latest_metric.get("risk_level") or "unknown"
        recovery = latest_metric.get("recovery_score")
        acwr = latest_metric.get("acwr")
        sleep = latest_health.get("sleep_hours")
        hrv = latest_health.get("hrv_avg")
        rhr = latest_health.get("resting_hr")
        stress = latest_health.get("stress_avg")

        lines = [
            "這是基於資料庫證據的 MVP 分析，不是醫療診斷。",
            f"今日恢復分數：{recovery if recovery is not None else '資料不足'}，訓練風險：{risk}。",
            f"睡眠 {sleep if sleep is not None else 'NA'} 小時、HRV {hrv if hrv is not None else 'NA'}、RHR {rhr if rhr is not None else 'NA'}、壓力 {stress if stress is not None else 'NA'}。",
            f"ACWR：{acwr if acwr is not None else '資料不足'}；最近資料範圍內共有 {len(activities)} 筆活動。",
        ]
        if risk == "high":
            lines.append("建議今天降低強度，優先安排恢復、有氧低強度或技術訓練。")
        elif risk == "medium":
            lines.append("建議保留訓練但控制總量，避免連續高強度刺激。")
        else:
            lines.append("若主觀疲勞感也低，可以安排計畫內訓練；仍建議觀察睡眠與 HRV 變化。")
        return "\n".join(lines)

