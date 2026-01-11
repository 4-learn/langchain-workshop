"""
Workshop 解答：任務 1 - 確認 LangChain 環境可以運作

執行方式：
python 01_check_environment.py

預期輸出：
Hello! How can I assist you today?
（或其他 LLM 的回應）
"""

from langchain_openai import ChatOpenAI

# 建立 LLM
llm = ChatOpenAI(model="gpt-4o-mini")

# 測試
response = llm.invoke("說 Hello")
print(response.content)
