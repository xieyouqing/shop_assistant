from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import config
from indexing.product_loader import load_products
import logging
import time


logger = logging.getLogger(__name__)

def products_to_documents(products:list)->list[Document]:
    if not products:
        logger.warning('商品列表为空，返回空文档')
        return []
    logger.info('开始将数据转化为Document格式')
    docs = []
    for p in products:
        specs_str = ' '.join(f"{k}{v}" for k, v in p['specs'].items())
        text = f"{p['name']} {p['category']} 价格{p['price']}元 库存{p['stock']} {specs_str} {' '.join(p['selling_points'])} {p['description']}"
        docs.append(Document(page_content=text, metadata = {"id": p["id"], "name": p["name"], "price": p["price"],"stock": p["stock"]}))
    logger.info('格式转换成功')
    return docs

def build()->dict:
    try:
        logger.info('开始建造向量库')
        start_time = time.time()
        chunks = products_to_documents(load_products())
        logger.info('开始加载embedding 模型,model_name:%s', config.EMBEDDING_MODEL_NAME)
        embedding = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        logger.info('embedding 模型加载完成,model_name:%s', config.EMBEDDING_MODEL_NAME)
        vectorstore = FAISS.from_documents(chunks, embedding)
        vectorstore.save_local(config.INDEX_DIR)
        build_time = time.time() - start_time
        logger.info('向量库建造成功，用时%d，路径%s', round(build_time, 2), config.INDEX_DIR)
        return {
            "num_chunks": len(chunks),
            "index_dir": config.INDEX_DIR,
            "build_time": round(build_time, 2)
        }
    except Exception as e:
        logger.error('向量库建造失败,错误%s',e)
        return {}

if __name__ == "__main__":
      build()