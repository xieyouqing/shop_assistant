import config
import logging
from retrieval.hybrid_retriever import HybridRetriever
import jieba


logger = logging.getLogger(__name__)
hybrid_retriever = HybridRetriever()

def search_product(query: str) -> str:
    results = hybrid_retriever.search(query)
    if not results:
        return "抱歉没有找到相关物品"
    # v1 粗兜底：query 分词后至少一个词命中结果，否则视为没找到
    keywords = [w for w in jieba.lcut(query) if len(w) > 1]
    if keywords and not any(w in doc.page_content for doc in results for w in keywords):
        return "抱歉，没有找到相关商品"
    logger.info('查询结束，返回%d个结果',len(results))
    return '\n\n'.join(doc.page_content for doc in results)