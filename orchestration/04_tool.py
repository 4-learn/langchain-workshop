"""
Workshop 解答：Tool - LLM 與系統的邊界

題目：
1. 定義「查詢法規」Tool
2. 定義「發送通知」Tool
3. 定義「記錄違規」Tool
4. bind_tools + AgentExecutor 自動執行

執行方式：
  python 04_tool.py

需要：
  pip install langchain langchain-google-genai python-dotenv
  .env 裡設定 GOOGLE_API_KEY
"""

from dotenv import load_dotenv
load_dotenv()

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from datetime import datetime


# 模擬資料庫
REGULATIONS_DB = {
    "安全帽": "職業安全衛生設施規則 第 281 條：雇主對於在高度二公尺以上之處所作業，勞工有墜落之虞者，應使勞工確實使用安全帽。",
    "反光背心": "職業安全衛生設施規則 第 277 條：雇主對於有車輛出入之場所，應設置反光標誌或使勞工穿著反光衣著。",
    "安全帶": "職業安全衛生設施規則 第 225 條：雇主對於在高度二公尺以上之處所作業，應使勞工確實使用安全帶。",
}

VIOLATION_LOG = []
NOTIFICATIONS = []


# 1. 查詢法規 Tool
@tool
def search_regulation(keyword: str) -> str:
    """搜尋工安法規

    Args:
        keyword: 搜尋關鍵字

    Returns:
        相關法規條文
    """
    for key, regulation in REGULATIONS_DB.items():
        if keyword in key or keyword in regulation:
            return regulation
    return f"找不到與「{keyword}」相關的法規"


# 2. 發送通知 Tool
@tool
def send_alert(message: str, level: str = "medium") -> str:
    """發送告警通知

    Args:
        message: 告警訊息
        level: 告警等級 (low/medium/high)

    Returns:
        發送結果
    """
    notification = {
        "message": message,
        "level": level,
        "timestamp": datetime.now().isoformat(),
    }
    NOTIFICATIONS.append(notification)
    return f"已發送 {level} 級別告警：{message}"


# 3. 記錄違規 Tool
@tool
def log_violation(
    violation_type: str,
    zone: str,
    description: str,
    severity: str = "medium"
) -> str:
    """記錄違規事件

    Args:
        violation_type: 違規類型
        zone: 發生區域
        description: 違規描述
        severity: 嚴重程度 (low/medium/high)

    Returns:
        記錄結果
    """
    record = {
        "id": f"V{len(VIOLATION_LOG) + 1:03d}",
        "type": violation_type,
        "zone": zone,
        "description": description,
        "severity": severity,
        "timestamp": datetime.now().isoformat(),
    }
    VIOLATION_LOG.append(record)
    return f"已記錄違規 {record['id']}：{description}"


# 測試
def main():
    print("=== Tool 測試 ===\n")

    # 收集 tools
    tools = [search_regulation, send_alert, log_violation]
    print(f"已定義 {len(tools)} 個 Tools:")
    for t in tools:
        print(f"  - {t.name}: {t.description[:50]}...")

    print("\n--- 測試 search_regulation ---")
    result = search_regulation.invoke({"keyword": "安全帽"})
    print(f"搜尋「安全帽」：{result[:80]}...")

    print("\n--- 測試 send_alert ---")
    result = send_alert.invoke({"message": "A區發現 PPE 違規", "level": "high"})
    print(result)

    print("\n--- 測試 log_violation ---")
    result = log_violation.invoke({
        "violation_type": "no_helmet",
        "zone": "construction",
        "description": "工人未配戴安全帽",
        "severity": "high"
    })
    print(result)

    # --- 任務 3：bind_tools ---
    print("\n--- 測試 bind_tools ---")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    llm_with_tools = llm.bind_tools(tools)

    response = llm_with_tools.invoke("幫我查安全帽的法規")
    print(f"LLM 選擇的 Tool：")
    for tc in response.tool_calls:
        print(f"  {tc['name']}({tc['args']})")

    # --- 任務 4：AgentExecutor ---
    print("\n--- 測試 AgentExecutor ---")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是工安助手，可以查詢法規、發送告警、記錄違規。用繁體中文回答。"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools)

    result = executor.invoke({"input": "A區有人沒戴安全帽，幫我查法規然後發 high 告警"})
    print(f"回答：{result['output'][:200]}")

    print("\n=== 測試完成 ===")
    print(f"通知記錄：{len(NOTIFICATIONS)} 筆")
    print(f"違規記錄：{len(VIOLATION_LOG)} 筆")


if __name__ == "__main__":
    main()
