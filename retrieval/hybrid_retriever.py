from langchain_core.documents import Document
import config
import logging
from retrieval.bm25_retriever import BM25RetrieverEngine
from retrieval.vector_retriever import VectorRetriever


logger = logging.getLogger(__name__)

class HybridRetriever:
    def __init__(self):
        logger.info('开始初始化混合检索器')
        self.vector_retriever = VectorRetriever()
        self.bm25_retriever = BM25RetrieverEngine()
        logger.info('混合检索器初始化完成')

    def reciprocal_rank_fusion(self,vector_results: list[Document], bm25_results: list[Document], k: int = config.RRF_K)->list[Document]:
        if not vector_results and not bm25_results:
            logger.warning("vector_results, bm25_results为空，返回空")
            return []
        if not vector_results:
            logger.info("vector_results为空")
        if not bm25_results:
            logger.info("bm25_results为空")
        try:
            logger.info("RRF融合开始：传入向量检索文档数量 = %d, 传入bm25检索文档数量 = %d", len(vector_results),len(bm25_results))
            doc_scores = {}
            for rank, doc in enumerate(vector_results):
                content = doc.page_content
                if content not in doc_scores:
                    doc_scores[content] = [0, doc]
                doc_scores[content][0] += 1 / (k + rank)

            for rank, doc in enumerate(bm25_results):
                content = doc.page_content
                if content not in doc_scores:
                    doc_scores[content] = [0, doc]
                doc_scores[content][0] += 1 / (k + rank)

            doc_scores = sorted(doc_scores.items(),key=lambda item: item[1][0],reverse=True)
            logger.info("RRF融合结束：返回文档数 = %d", len(doc_scores))
            return [doc for _, (_, doc) in doc_scores]
        except Exception as e:
            logger.error("RRF融合失败，返回空，错误： %s", e)
            return []

    def search(self,query:str)-> list[Document]:
        bm25_results = self.bm25_retriever.search(query)
        vector_results = self.vector_retriever.search(query)
        results = self.reciprocal_rank_fusion(vector_results,bm25_results)
        if not results:
            logger.warning("RRF融合返回结果为空，混合检索返回空")
            return []
        return results[:config.HYBRID_TOP_N]

