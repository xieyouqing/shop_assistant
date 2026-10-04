import config
import logging
from agent.router import router
from agent.answer import answer
from retrieval.product_search import search_product


logger = logging.getLogger(__name__)

history = []

current = []

def handle_turn(query):
    global current
    try:
        route = router(query)

        if route["route"]=="product":
            q = " ".join(current) if (route["has_pronoun"] and current) else query
            doc = search_product(q)
            result = answer(query, history, doc)
            current = result["current"]
            history.append({"role": "user", "content": query})
            history.append({"role": 'assistant', "content": result["answer"]})

        else:
            result = answer(query,history)
            history.append({"role":"user","content":query})
            history.append({"role": 'assistant', "content": result["answer"]})

        return result["answer"]

    except Exception as e:
        logger.error("生成回复失败 %s", e)
        return "网络错误，请重新输入"
