"""
Workshop 解答：任務 4 - 多步驟 Chain

Chain 1：分析嚴重程度
Chain 2：生成告警訊息

執行方式：
  python 04_multi_step_chain.py

需要：
  pip install langchain langchain-google-genai python-dotenv
  .env 裡設定 GOOGLE_API_KEY
"""

from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def main():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

    # Chain 1：分析嚴重程度
    analyze_prompt = ChatPromptTemplate.from_messages([
        ("system", "分析違規事件的嚴重程度，只回答：低、中、高"),
        ("human", "違規事件：{violation}")
    ])
    analyze_chain = analyze_prompt | llm | StrOutputParser()

    # Chain 2：生成告警
    alert_prompt = ChatPromptTemplate.from_messages([
        ("system", "根據違規和嚴重程度，生成一句告警訊息"),
        ("human", "違規：{violation}\n嚴重程度：{severity}")
    ])
    alert_chain = alert_prompt | llm | StrOutputParser()

    # 測試
    violations = [
        "A區工人沒戴安全帽",
        "B區通道堆放雜物",
        "C區高空作業未繫安全帶",
    ]

    for v in violations:
        print(f"\n{'─' * 50}")
        print(f"違規：{v}")

        severity = analyze_chain.invoke({"violation": v})
        print(f"嚴重程度：{severity}")

        alert = alert_chain.invoke({"violation": v, "severity": severity})
        print(f"告警訊息：{alert}")


if __name__ == "__main__":
    main()
