import config
import logging
from typing import List
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder


logger = logging.getLogger(__name__)

class Reranker:
    def __init__(self,model: str =config.RERANKER_MODEL_NAME):
        logger.info("开始加载Reranker 模型： %s",model)
        # RTX 5060 (sm_120) 当前 torch 2.6.0 不支持，强制 CPU 运行；
        # 升级 torch 到支持 Blackwell 的版本后可改回 GPU
        try:
            self.model = CrossEncoder(model_name=model, device="cpu")
            logger.info("Reranker 模型加载完成")
        except Exception as e:
            logger.error("Reranker 加载失败，降级为不精排：%s", e)
            self.model = None

    def rerank(self, query: str, documents: List[Document], top_k: int = config.RERANKER_TOP_N,
               score_threshold: float = config.RERANKER_SCORE_THRESHOLD) -> List[Document]:
        if not documents:
            logger.warning("传入文档为空，返回空列表")
            return []
        if not self.model:
            logger.error("Reranker 加载失败，降级为不精排,返回原文档")
            return [doc for doc in documents]
        try:
            pairs = [(query, doc.page_content) for doc in documents]
            scores = self.model.predict(pairs)
            logger.info("计分完成，文档数： %s", len(documents))
            scores_doc = list(zip(documents, scores))
            scores_doc.sort(key=lambda x: x[1], reverse=True)
            # 先取 top_k，再把分数低于阈值的"边缘文档"剔除，宁缺毋滥
            top_picks = scores_doc[:top_k]
            result = [doc for doc, s in top_picks if s >= score_threshold]
            logger.info("Reranker 重排序完成：top%d 分数 %s，剔除低分后返回 %d 个（阈值 %.2f）",
                        top_k, [round(float(s), 3) for _, s in top_picks], len(result), score_threshold)
            return result

        except Exception as e:
            logger.error("Reranker 重排序失败： %s", e)
            return documents[:top_k]