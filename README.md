# LangChain Workshop

行為層（Orchestration）的 Workshop 解答 - 決策編排。

## 目錄

| 目錄 | 說明 |
|------|------|
| `orchestration/` | 行為編排：Chain、Tool、Agent 整合 |

## 安裝

```bash
pip install langchain langchain-openai python-dotenv pydantic
```

## 設定

```bash
export OPENAI_API_KEY="your-api-key"
```

## 執行

```bash
# 行為編排 Workshop（可用無 API 模式）
python orchestration/solution.py
```

## 注意事項

- 不設定 API Key 也可執行（使用規則式 fallback）
- 設定 API Key 後可測試完整 LLM 功能
- Agent verbose 模式會顯示工具呼叫過程
