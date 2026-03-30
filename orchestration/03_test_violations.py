"""
Workshop 解答：任務 3 - 測試不同的違規事件

執行方式：
python 03_test_violations.py

預期輸出：
=== 測試 1：工人沒戴安全帽 ===
違規類型：PPE 違規
嚴重程度：高
...

=== 測試 2：機台旁邊有積水 ===
違規類型：環境安全違規
嚴重程度：中
...

=== 測試 3：員工在禁煙區抽煙 ===
違規類型：消防安全違規
嚴重程度：高
...
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 建立 Chain
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是工安專家。分析違規事件，回答違規類型和嚴重程度。"),
    ("human", "{violation}")
])

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
parser = StrOutputParser()

chain = prompt | llm | parser

# 測試案例
test_cases = [
    "工人沒戴安全帽",
    "機台旁邊有積水",
    "員工在禁煙區抽煙",
]

# 執行測試
for i, violation in enumerate(test_cases, 1):
    print(f"=== 測試 {i}：{violation} ===")
    result = chain.invoke({"violation": violation})
    print(result)
    print()
