import config
import logging
from retrieval.hybrid_retriever import HybridRetriever
from reranker import Reranker

logger = logging.getLogger(__name__)
hybrid_retriever = HybridRetriever()
reranker = Reranker()

def search_product(query: str) -> str:
    docs = hybrid_retriever.search(query)
    logger.info('查询结束，返回%d个结果',len(docs))
    results = reranker.rerank(query,docs)
    if  not results:
        return "抱歉，没有找到相关商品"
    return '\n\n'.join(doc.page_content for doc in results)