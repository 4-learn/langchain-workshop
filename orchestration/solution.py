"""
Workshop 解答：LangChain 行為編排

題目要求：
1. 實作違規分析 Chain
2. 定義工安系統 Tools
3. 建立工安助手 Agent
4. 整合成完整系統

預期輸出：
=== 工安行為編排系統 ===

輸入: 分析今天的違規狀況，並給出改善建議

Agent 執行中...
> 使用工具: get_statistics
> 結果: 總違規 4 件...
> 使用工具: query_violations
> 結果: [V001] construction: no_helmet...
> 使用工具: lookup_regulation
> 結果: 職業安全衛生設施規則 第 281 條...

最終回答:
今日共有 4 件違規，其中施工區安全帽違規最多...
建議立即加強施工區入口 PPE 檢查...
"""

import os
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Callable
from abc import ABC, abstractmethod

# 嘗試載入 LangChain（可選）
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
    from langchain_core.tools import tool, StructuredTool
    from langchain_core.runnables import RunnableLambda
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    from pydantic import BaseModel, Field
    from dotenv import load_dotenv
    load_dotenv()
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


# === 資料結構 ===

@dataclass
class ViolationRecord:
    """違規記錄"""
    id: str
    timestamp: datetime
    zone: str
    violation_type: str
    confidence: float
    severity: str
    description: str = ""


@dataclass
class AnalysisResult:
    """分析結果"""
    summary: str
    total_violations: int
    high_priority_count: int
    recommendations: list
    regulations: list


# === 資料存取層 ===

class SafetyDataAccess:
    """資料存取層（模擬資料庫）"""

    def __init__(self):
        self._violations = [
            ViolationRecord("V001", datetime.now(timezone.utc), "construction", "no_helmet", 0.92, "high", "施工區人員未戴安全帽"),
            ViolationRecord("V002", datetime.now(timezone.utc), "entrance", "no_vest", 0.78, "medium", "入口處人員未穿反光背心"),
            ViolationRecord("V003", datetime.now(timezone.utc), "construction", "no_helmet", 0.85, "high", "施工區另一人員未戴安全帽"),
            ViolationRecord("V004", datetime.now(timezone.utc), "warehouse", "blocked_exit", 0.65, "medium", "倉庫緊急出口被阻擋"),
            ViolationRecord("V005", datetime.now(timezone.utc), "construction", "no_safety_belt", 0.88, "high", "高空作業未繫安全帶"),
        ]

        self._regulations = {
            "no_helmet": ("職業安全衛生設施規則 第 281 條", "雇主對於在高度二公尺以上之處所作業，勞工有墜落之虞者，應使勞工確實使用安全帽。"),
            "no_vest": ("職業安全衛生設施規則 第 277 條", "雇主對於有車輛出入之場所，應設置反光標誌或使勞工穿著反光衣著。"),
            "no_safety_belt": ("職業安全衛生設施規則 第 225 條", "雇主對於在高度二公尺以上之處所作業，應使勞工確實使用安全帶。"),
            "blocked_exit": ("職業安全衛生設施規則 第 33 條", "緊急出口及通道應保持暢通，不得堆積物品。"),
        }

    def get_violations(self, zone: str = None, severity: str = None) -> list:
        result = self._violations
        if zone:
            result = [v for v in result if v.zone == zone]
        if severity:
            result = [v for v in result if v.severity == severity]
        return result

    def get_statistics(self) -> dict:
        by_zone = {}
        by_type = {}
        by_severity = {}
        for v in self._violations:
            by_zone[v.zone] = by_zone.get(v.zone, 0) + 1
            by_type[v.violation_type] = by_type.get(v.violation_type, 0) + 1
            by_severity[v.severity] = by_severity.get(v.severity, 0) + 1
        return {
            "total": len(self._violations),
            "by_zone": by_zone,
            "by_type": by_type,
            "by_severity": by_severity
        }

    def get_regulation(self, violation_type: str) -> tuple:
        return self._regulations.get(violation_type, ("", ""))


# === Tools 定義 ===

def create_tools(data_access: SafetyDataAccess):
    """建立工安系統 Tools"""

    if not LANGCHAIN_AVAILABLE:
        return []

    @tool
    def query_violations(zone: Optional[str] = None, severity: Optional[str] = None) -> str:
        """查詢違規記錄

        Args:
            zone: 區域篩選（construction, entrance, warehouse, office）
            severity: 嚴重程度篩選（high, medium, low）

        Returns:
            違規記錄列表
        """
        violations = data_access.get_violations(zone, severity)
        if not violations:
            return "沒有符合條件的違規記錄"

        lines = []
        for v in violations:
            lines.append(f"[{v.id}] {v.zone} - {v.violation_type} ({v.severity}): {v.description}")
        return "\n".join(lines)

    @tool
    def get_statistics() -> str:
        """取得今日違規統計摘要

        Returns:
            統計摘要
        """
        stats = data_access.get_statistics()
        lines = [
            f"今日違規總數: {stats['total']} 件",
            "",
            "依區域統計:"
        ]
        for zone, count in stats["by_zone"].items():
            lines.append(f"  - {zone}: {count} 件")

        lines.append("")
        lines.append("依類型統計:")
        for vtype, count in stats["by_type"].items():
            lines.append(f"  - {vtype}: {count} 件")

        lines.append("")
        lines.append("依嚴重程度:")
        for sev, count in stats["by_severity"].items():
            lines.append(f"  - {sev}: {count} 件")

        return "\n".join(lines)

    @tool
    def lookup_regulation(violation_type: str) -> str:
        """查詢違規類型對應的法規

        Args:
            violation_type: 違規類型代碼（no_helmet, no_vest, no_safety_belt, blocked_exit）

        Returns:
            法規名稱和內容
        """
        title, content = data_access.get_regulation(violation_type)
        if not title:
            return f"找不到 {violation_type} 對應的法規"
        return f"【{title}】\n{content}"

    @tool
    def send_alert(message: str, level: str = "info") -> str:
        """發送告警通知

        Args:
            message: 告警訊息
            level: 告警級別（urgent, warning, info）

        Returns:
            發送結果
        """
        print(f"[ALERT-{level.upper()}] {message}")
        return f"已發送 {level} 級別告警"

    return [query_violations, get_statistics, lookup_regulation, send_alert]


# === Chain 實作 ===

class SafetyAnalysisChain:
    """違規分析 Chain（固定流程）"""

    def __init__(self, data_access: SafetyDataAccess):
        self.data_access = data_access

        if LANGCHAIN_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self._setup_chain()
        else:
            self.chain = None

    def _setup_chain(self):
        """設定 Chain"""

        class AnalysisOutput(BaseModel):
            summary: str = Field(description="違規狀況摘要")
            key_issues: list = Field(description="主要問題列表")
            recommendations: list = Field(description="改善建議")

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        parser = JsonOutputParser(pydantic_object=AnalysisOutput)

        prompt = ChatPromptTemplate.from_template("""
你是工安分析專家。根據以下資料分析違規狀況。

統計資料：
{statistics}

違規列表：
{violations}

請提供：
1. 簡潔的摘要
2. 主要問題
3. 具體改善建議

{format_instructions}
""")

        def prepare_data(input_dict):
            stats = self.data_access.get_statistics()
            violations = self.data_access.get_violations()
            return {
                "statistics": str(stats),
                "violations": "\n".join([f"{v.zone}: {v.violation_type}" for v in violations]),
            }

        self.chain = (
            RunnableLambda(prepare_data)
            | prompt.partial(format_instructions=parser.get_format_instructions())
            | llm
            | parser
        )

    def analyze(self) -> dict:
        """執行分析"""
        if self.chain:
            return self.chain.invoke({})
        else:
            # Fallback: 規則式分析
            return self._rule_based_analysis()

    def _rule_based_analysis(self) -> dict:
        """規則式分析（不需 LLM）"""
        stats = self.data_access.get_statistics()
        violations = self.data_access.get_violations()

        high_count = stats["by_severity"].get("high", 0)

        return {
            "summary": f"今日共 {stats['total']} 件違規，其中 {high_count} 件為高風險",
            "key_issues": [
                f"{vtype}: {count} 件"
                for vtype, count in stats["by_type"].items()
            ],
            "recommendations": [
                "加強施工區 PPE 檢查" if "construction" in stats["by_zone"] else "",
                "高風險違規需立即處理" if high_count > 0 else "",
            ]
        }


# === Agent 實作 ===

class SafetyAssistantAgent:
    """工安助手 Agent"""

    def __init__(self, data_access: SafetyDataAccess):
        self.data_access = data_access
        self.tools = create_tools(data_access)

        if LANGCHAIN_AVAILABLE and os.getenv("OPENAI_API_KEY") and self.tools:
            self._setup_agent()
        else:
            self.executor = None

    def _setup_agent(self):
        """設定 Agent"""
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是工安監控系統的 AI 助手。

職責：
1. 查詢和分析違規記錄
2. 提供統計摘要
3. 查詢相關法規
4. 需要時發送告警

回答要求：
- 使用繁體中文
- 提供具體數據
- 引用法規時說明條文
- 給出可執行的建議"""),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(llm, self.tools, prompt)

        self.executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )

    def chat(self, message: str) -> str:
        """對話"""
        if self.executor:
            result = self.executor.invoke({"input": message})
            return result["output"]
        else:
            # Fallback: 簡單回應
            return self._simple_response(message)

    def _simple_response(self, message: str) -> str:
        """簡單回應（不需 LLM）"""
        if "統計" in message or "多少" in message:
            stats = self.data_access.get_statistics()
            return f"今日違規統計：共 {stats['total']} 件違規"
        elif "法規" in message:
            return "請指定違規類型以查詢相關法規"
        else:
            return "我是工安助手，可以查詢違規記錄、統計資料和相關法規。"


# === 整合系統 ===

class SafetyOrchestrator:
    """
    工安行為編排系統

    整合 Chain 和 Agent，提供統一介面
    """

    def __init__(self):
        self.data_access = SafetyDataAccess()
        self.chain = SafetyAnalysisChain(self.data_access)
        self.agent = SafetyAssistantAgent(self.data_access)

    def analyze(self) -> dict:
        """執行分析（使用 Chain）"""
        return self.chain.analyze()

    def chat(self, message: str) -> str:
        """對話（使用 Agent）"""
        return self.agent.chat(message)

    def get_status(self) -> dict:
        """取得系統狀態"""
        stats = self.data_access.get_statistics()
        return {
            "total_violations": stats["total"],
            "high_priority": stats["by_severity"].get("high", 0),
            "chain_available": self.chain.chain is not None,
            "agent_available": self.agent.executor is not None,
        }


# === 主程式 ===

def main():
    print("=" * 50)
    print("LangChain Workshop: 工安行為編排系統")
    print("=" * 50)
    print()

    # 建立系統
    orchestrator = SafetyOrchestrator()

    # 顯示狀態
    status = orchestrator.get_status()
    print("系統狀態:")
    print(f"  總違規數: {status['total_violations']}")
    print(f"  高優先: {status['high_priority']}")
    print(f"  Chain 可用: {status['chain_available']}")
    print(f"  Agent 可用: {status['agent_available']}")

    # 執行分析（Chain）
    print("\n" + "=" * 50)
    print("執行分析（Chain）")
    print("=" * 50)

    result = orchestrator.analyze()
    print(f"\n摘要: {result['summary']}")
    print(f"主要問題: {result['key_issues']}")
    print(f"建議: {result['recommendations']}")

    # 互動對話（Agent）
    print("\n" + "=" * 50)
    print("互動對話（Agent）")
    print("=" * 50)

    test_messages = [
        "今天有多少違規？",
        "施工區的違規有哪些？",
    ]

    for msg in test_messages:
        print(f"\n用戶: {msg}")
        response = orchestrator.chat(msg)
        print(f"助手: {response}")

    # 如果有 API Key，測試完整 Agent
    if LANGCHAIN_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        print("\n" + "-" * 50)
        print("完整 Agent 測試")
        print("-" * 50)

        complex_query = "分析今天的違規狀況，找出最嚴重的問題，並告訴我相關法規"
        print(f"\n用戶: {complex_query}")
        response = orchestrator.chat(complex_query)
        print(f"\n助手: {response}")

    print("\nWorkshop 完成！")


if __name__ == "__main__":
    main()
