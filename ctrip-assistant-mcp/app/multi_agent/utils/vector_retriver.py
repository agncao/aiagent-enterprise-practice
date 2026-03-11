import os
import pathlib
import re

import numpy as np
from dashscope import TextEmbedding
from config import CONFIG,get_logger
logger = get_logger(__name__)

class VectorStoreRetriever:
    def __init__(self,documents,vectors):
        self._documents = documents
        self._vectors = vectors
    
    @staticmethod
    def read_raw_documents(path_file_name:str, pattern:str) -> list[dict]:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        md_path = pathlib.Path(path_file_name)
        if not md_path.is_absolute():
            md_path = pathlib.Path(os.path.join(base_dir, path_file_name))
        if not md_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {md_path}")

        content = md_path.read_text(encoding="utf-8")
        documents = [
            {"page_content": block.strip()}
            for block in re.split(pattern, content)
            if isinstance(block, str) and block.strip()
        ]
        return documents


    @classmethod
    def embedding(cls, path:str, pattern:str):
        '''
        将文本转化为通义千问的Embedding格式
        '''
        documents = VectorStoreRetriever.read_raw_documents(path, pattern)
        contents = [
            doc["page_content"] 
            for doc in documents
            if isinstance(doc.get("page_content"), str) and doc["page_content"].strip()
        ]
        logger.info(f"Embedding model: {CONFIG['embedding']['model']}")
        response = TextEmbedding.call(
            model=CONFIG["embedding"]["model"],
            input=contents,
            api_key=CONFIG["embedding"]["api_key"],
            dimension=CONFIG["embedding"]["dimension"]
        )
        # vectors = [doc_emb for i, doc_emb in enumerate(response.output['embeddings'])]
        vectors = [
            np.asarray(item["embedding"], dtype=float)
            for item in response.output["embeddings"]
            if "embedding" in item
        ]
        return cls(documents, vectors)
    
    # 计算余弦相似度
    def cosine_similarity(self, a, b):
        a_arr = np.asarray(a, dtype=float)
        b_arr = np.asarray(b, dtype=float)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))

    def semantic_search(self, query:str, top_k=5):
        """语义搜索"""
        # 生成查询向量
        query_embedding_response = TextEmbedding.call(
            model=CONFIG["embedding"]["model"],
            input=query,
            api_key=CONFIG["embedding"]["api_key"],
            dimension=CONFIG["embedding"]["dimension"]
        )["output"]["embeddings"]
        if not query_embedding_response:
            return []
        query_embedding = np.asarray(query_embedding_response[0]["embedding"], dtype=float)

        # 计算相似度
        similarities = []
        for i, doc_emb in enumerate(self._vectors):
            similarity = self.cosine_similarity(query_embedding, doc_emb)
            similarities.append((i, similarity))

        # 排序并返回top_k结果
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [(self._documents[i], sim) for i, sim in similarities[:top_k]]


if __name__ == "__main__":
    vector_retriver = VectorStoreRetriever.embedding(CONFIG["order_faq"]["path"], r"(?=\n##)")
    # print(vector_retriver._vectors[0])
    # results = vector_retriver.semantic_search("怎么才能退票呢？", top_k=2)
    # for doc, sim in results:
    #     print(doc["page_content"])
    #     print("="*50)
