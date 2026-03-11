from langchain_core.tools import tool
from app.multi_agent.utils.vector_retriver import VectorStoreRetriever
from config import CONFIG

@tool
def lookup_policy(query: str) -> str:
    """查询公司政策，检查某些选项是否允许。
    在进行航班变更或其他'写'操作之前使用此函数。"""
    
    vector_retriver = VectorStoreRetriever.embedding(CONFIG["order_faq"]["path"], r"(?=\n##)")
    results = vector_retriver.semantic_search(query, top_k=2)
    return "\n\n".join([doc["page_content"] for doc, _ in results])

if __name__ == "__main__":
    print(lookup_policy.invoke({'query': '怎么才能退票呢？'}))
