import config
import logging
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


logger = logging.getLogger(__name__)

class VectorRetriever:
    def __init__(self):
        try:
            logger.info('开始创建embeddings模型')
            self.embeddings = HuggingFaceEmbeddings(
                model_name=config.EMBEDDING_MODEL_NAME,
                model_kwargs={"device": 'cpu'},
                encode_kwargs={"normalize_embeddings": True}
            )
            logger.info('embeddings模型创建成功')
        except Exception as e:
            self.embeddings = None
            logger.error('embeddings模型创建失败，错误：%s',e)
        try:
            logger.info("开始加载向量索引： %s",config.INDEX_DIR)
            if self.embeddings is None:
                logger.error('embeddings模型不可用')
                self.vectorstore=None
            else:
                self.vectorstore =FAISS.load_local(config.INDEX_DIR,self.embeddings,allow_dangerous_deserialization=True)
                logger.info('向量索引加载成功')
        except Exception as e:
            self.vectorstore = None
            logger.error('向量索引加载失败，错误：%s',e)

    def search(self,query:str,k:int=config.VECTOR_SEARCH_K)->list[Document]:
        if self.vectorstore is None:
            logger.warning('向量索引不可用，返回空')
            return []
        try:
            docs = self.vectorstore.similarity_search(query,k = k)
            logger.debug("查询成功，返回结果： top_k = %d", len(docs))
            return docs
        except Exception as e:
            logger.error("查询失败，返回空，错误： %s",e)
            return []