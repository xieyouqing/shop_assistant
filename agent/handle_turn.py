import config
import logging
from agent.router import router
from agent.answer import answer
from retrieval.product_search import search_product


logger = logging.getLogger(__name__)

class HandleTurn:
    def __init__(self):
        self.history = []
        self.current = []


    def handle_turn(self,query):
        try:
            route = router(query)

            if route["route"]=="product":
                q = " ".join(self.current) if (route["has_pronoun"] and self.current) else query
                doc = search_product(q)
                result = answer(query, self.history, doc)
                self.current = result["current"]
                self.history.append({"role": "user", "content": query})
                self.history.append({"role": 'assistant', "content": result["answer"]})

            else:
                result = answer(query,self.history)
                self.history.append({"role":"user","content":query})
                self.history.append({"role": 'assistant', "content": result["answer"]})

            return result["answer"]

        except Exception as e:
            logger.error("生成回复失败 %s", e)
            return "网络错误，请重新输入"
