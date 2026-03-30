"""
Workshop 解答：任務 2 - 建立你的第一個 Chain

執行方式：
python 02_first_chain.py

預期輸出：
違規類型：PPE 違規（個人防護裝備）
嚴重程度：高

分析：
- 未配戴安全帽屬於 PPE 違規
- 在施工區域，這是高嚴重程度的違規
- 可能違反職業安全衛生法規
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. 建立 Prompt 模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是工安專家。分析違規事件，回答違規類型和嚴重程度。"),
    ("human", "{violation}")
])

# 2. 建立 LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# 3. 建立 Parser
parser = StrOutputParser()

# 4. 組合成 Chain（使用 | 運算子）
chain = prompt | llm | parser

# 5. 執行
result = chain.invoke({"violation": "工人沒戴安全帽"})
print(result)
