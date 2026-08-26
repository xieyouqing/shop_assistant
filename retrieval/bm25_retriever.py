from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
import jieba
import config
import logging
from indexing.product_loader import load_products
from indexing.build_index import products_to_documents


logger = logging.getLogger(__name__)

class BM25RetrieverEngine:
    def __init__(self):
        try:
            docs = products_to_documents(load_products())
            logger.info('开始创建BM25检索器')
            self.retriever = BM25Retriever.from_documents(
                documents= docs,
                preprocess_func=lambda text:jieba.lcut(text)
            )
            logger.info('BM25检索器创建成功')
        except Exception as e:
            self.retriever = None
            logger.error('BM25检索器创建失败，错误：%s',e)

    def search(self,ques:str,k:int=config.BM25_SEARCH_K)->list[Document]:
        if self.retriever is None:
            logger.warning('BM25检索器不可以，返回空')
            return []
        try:
            logger.info('BM25检索器开始搜索')
            self.retriever.k =k
            results = self.retriever.invoke(ques)
            logger.info('BM25检索器搜索完成，返回%d',len(results))
            return results
        except Exception as e:
            logger.error('BM25检索器搜索失败，错误：%s',e)
            return []