"""
Workshop 解答：Chain - 線性行為流程

題目：
1. 建立「分析違規」Chain
2. 建立「查詢法規」Chain
3. 建立「生成報告」Chain
4. 組合成完整流程

執行方式：
python 05_chain.py
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
import os


def main():
    # 檢查 API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("請設定 OPENAI_API_KEY 環境變數")
        print("使用模擬模式展示 Chain 結構...")
        demo_chain_structure()
        return

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 1. 分析違規 Chain
    analyze_prompt = ChatPromptTemplate.from_messages([
        ("system", """分析違規事件，以 JSON 格式回答：
{{"type": "違規類型", "severity": "high/medium/low", "description": "簡短描述"}}
只輸出 JSON，不要其他文字。"""),
        ("human", "違規事件：{violation}")
    ])

    analyze_chain = analyze_prompt | llm | StrOutputParser()

    # 2. 查詢法規 Chain
    regulation_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是法規專家。根據違規類型，提供相關的職業安全衛生法規。"),
        ("human", "違規類型：{type}\n請提供相關法規條文。")
    ])

    regulation_chain = regulation_prompt | llm | StrOutputParser()

    # 3. 生成報告 Chain
    report_prompt = ChatPromptTemplate.from_messages([
        ("system", "根據分析結果和法規，生成正式的違規報告。"),
        ("human", """
違規分析：{analysis}
相關法規：{regulation}

請生成一份簡潔的違規報告。""")
    ])

    report_chain = report_prompt | llm | StrOutputParser()

    # 4. 組合成完整流程
    def parse_analysis(text):
        import json
        try:
            return json.loads(text)
        except:
            return {"type": "unknown", "severity": "medium", "description": text}

    full_chain = (
        {"violation": RunnablePassthrough()}
        | RunnableLambda(lambda x: {"violation": x["violation"]})
        | analyze_chain
        | RunnableLambda(lambda x: {"analysis": x, "type": parse_analysis(x).get("type", "unknown")})
        | RunnableLambda(lambda x: {
            "analysis": x["analysis"],
            "regulation": regulation_chain.invoke({"type": x["type"]})
        })
        | report_chain
    )

    # 執行測試
    print("=== Chain 流程測試 ===\n")

    violation = "工人未戴安全帽"
    print(f"輸入：{violation}\n")

    # 逐步執行
    print("→ 步驟 1：分析違規")
    analysis = analyze_chain.invoke({"violation": violation})
    print(f"  結果：{analysis}\n")

    print("→ 步驟 2：查詢法規")
    regulation = regulation_chain.invoke({"type": "未配戴PPE"})
    print(f"  結果：{regulation[:100]}...\n")

    print("→ 步驟 3：生成報告")
    report = report_chain.invoke({"analysis": analysis, "regulation": regulation})
    print(f"  結果：\n{report}\n")

    print("=== 完成 ===")


def demo_chain_structure():
    """無 API Key 時展示 Chain 結構"""
    print("""
=== Chain 結構展示 ===

1. 分析違規 Chain：
   analyze_prompt | llm | StrOutputParser()

2. 查詢法規 Chain：
   regulation_prompt | llm | StrOutputParser()

3. 生成報告 Chain：
   report_prompt | llm | StrOutputParser()

4. 完整流程：
   輸入 → 分析違規 → 解析 JSON → 查詢法規 → 生成報告 → 輸出

模擬執行結果：
輸入：工人未戴安全帽
→ 分析：{"type": "未配戴PPE", "severity": "high", "description": "工人未配戴安全帽"}
→ 法規：職業安全衛生設施規則第 281 條...
→ 報告：[違規報告] A區發現工人未配戴安全帽，違反職安法規...
""")


if __name__ == "__main__":
    main()
