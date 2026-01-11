"""
Workshop 解答：Agent - 受控的行為選擇

題目：
1. 定義 Agent 需要的 Tools
2. 設計 Agent 的 System Prompt
3. 測試各種違規情境

執行方式：
python 06_agent.py
"""

import os
from datetime import datetime
from langchain_core.tools import tool


# === 1. 定義 Tools ===

REGULATIONS_DB = {
    "安全帽": "職業安全衛生設施規則 第 281 條：雇主應使勞工確實使用安全帽。",
    "反光背心": "職業安全衛生設施規則 第 277 條：有車輛出入之場所應穿著反光衣著。",
    "安全帶": "職業安全衛生設施規則 第 225 條：高處作業應使用安全帶。",
}


@tool
def analyze_violation(description: str) -> str:
    """分析違規事件的類型和嚴重程度

    Args:
        description: 違規事件描述

    Returns:
        分析結果
    """
    # 簡單規則分析
    if "安全帽" in description or "頭盔" in description:
        return "類型：未配戴PPE（安全帽）\n嚴重程度：高\n原因：頭部傷害風險"
    elif "反光" in description or "背心" in description:
        return "類型：未配戴PPE（反光背心）\n嚴重程度：中\n原因：能見度不足"
    elif "安全帶" in description:
        return "類型：未配戴PPE（安全帶）\n嚴重程度：高\n原因：墜落風險"
    else:
        return "類型：其他違規\n嚴重程度：待評估\n原因：需要進一步調查"


@tool
def search_regulation(keyword: str) -> str:
    """搜尋相關工安法規

    Args:
        keyword: 搜尋關鍵字

    Returns:
        相關法規
    """
    for key, reg in REGULATIONS_DB.items():
        if keyword in key:
            return reg
    return f"找不到與「{keyword}」相關的法規"


@tool
def send_alert(message: str, level: str) -> str:
    """發送告警通知

    Args:
        message: 告警訊息
        level: 告警等級 (low/medium/high)

    Returns:
        發送結果
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}] 已發送 {level.upper()} 級別告警：{message}"


@tool
def log_violation(violation_type: str, zone: str, action_taken: str) -> str:
    """記錄違規處理結果

    Args:
        violation_type: 違規類型
        zone: 發生區域
        action_taken: 採取的行動

    Returns:
        記錄結果
    """
    record_id = f"V{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return f"違規記錄 {record_id} 已建立\n類型：{violation_type}\n區域：{zone}\n處理：{action_taken}"


# === 2. Agent System Prompt ===

SYSTEM_PROMPT = """你是工安監控系統的 AI 助手。

你的職責是處理工安違規事件。收到違規報告時，請依照以下步驟處理：

1. 使用 analyze_violation 分析違規類型和嚴重程度
2. 使用 search_regulation 查詢相關法規
3. 根據嚴重程度決定告警等級：
   - 高風險：使用 send_alert 發送 high 級別告警
   - 中風險：使用 send_alert 發送 medium 級別告警
   - 低風險：直接記錄，不發送告警
4. 使用 log_violation 記錄處理結果

回答要求：
- 使用繁體中文
- 說明你的判斷依據
- 列出已執行的動作
"""


def main():
    tools = [analyze_violation, search_regulation, send_alert, log_violation]

    print("=== Agent 設定 ===\n")
    print("Tools:")
    for t in tools:
        print(f"  - {t.name}")

    print(f"\nSystem Prompt:\n{SYSTEM_PROMPT[:200]}...\n")

    # 檢查 API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("請設定 OPENAI_API_KEY 環境變數")
        print("\n使用模擬模式展示 Agent 行為...\n")
        demo_agent_behavior()
        return

    # 建立 Agent
    from langchain_openai import ChatOpenAI
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # 3. 測試各種情境
    test_cases = [
        "A區有人沒戴安全帽",
        "倉庫入口有人沒穿反光背心",
        "高空作業人員未繫安全帶",
    ]

    print("=== 測試情境 ===\n")
    for case in test_cases:
        print(f"\n--- 輸入：{case} ---\n")
        result = executor.invoke({"input": case})
        print(f"\n結果：{result['output']}\n")
        print("-" * 50)


def demo_agent_behavior():
    """模擬 Agent 行為"""
    print("--- 模擬：A區有人沒戴安全帽 ---\n")

    print("Agent 思考：需要先分析這個違規事件")
    print("Agent 行動：analyze_violation('A區有人沒戴安全帽')")
    result = analyze_violation.invoke({"description": "A區有人沒戴安全帽"})
    print(f"結果：{result}\n")

    print("Agent 思考：這是高風險違規，需要查詢相關法規")
    print("Agent 行動：search_regulation('安全帽')")
    result = search_regulation.invoke({"keyword": "安全帽"})
    print(f"結果：{result}\n")

    print("Agent 思考：需要發送高級別告警")
    print("Agent 行動：send_alert('A區發現未配戴安全帽', 'high')")
    result = send_alert.invoke({"message": "A區發現未配戴安全帽", "level": "high"})
    print(f"結果：{result}\n")

    print("Agent 思考：記錄這次違規處理")
    print("Agent 行動：log_violation(...)")
    result = log_violation.invoke({
        "violation_type": "未配戴PPE",
        "zone": "A區",
        "action_taken": "已發送高級別告警"
    })
    print(f"結果：{result}\n")

    print("Agent 輸出：已處理 A 區的安全帽違規，發送高優先級告警並完成記錄。")


if __name__ == "__main__":
    main()
