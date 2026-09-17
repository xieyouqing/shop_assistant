import config
import logging
from agent.router import router,rewrite
from agent.answer import answer
from retrieval.product_search import search_product


logger = logging.getLogger(__name__)

history = []

def handle_turn(query):
    try:
        route = router(query)
        if route=="product":
            recent = history[-4:]
            history_text = "\n".join(f"{m['role']}:{m['content']}" for m in recent)
            query_1 = rewrite(query,history_text)
            doc = search_product(query_1)
            result = answer(query,history,doc)
            history.append({"role":"user","content":query})
            history.append({"role": 'assistant', "content": result})

        else:
            result = answer(query,history)
            history.append({"role":"user","content":query})
            history.append({"role": 'assistant', "content": result})

        return result

    except Exception as e:
        logger.error("生成回复失败 %s", e)
        return "网络错误，请重新输入"