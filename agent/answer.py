import config
import logging
from agent.prompt import ANSWER_PROMPT
from agent.llm import call_llm
import json


logger = logging.getLogger(__name__)


answer_tool = [{
    "type": "function",
    "function": {
        "name": "current_shop",
        "description": "根据检索结果生成给用户的回复，并报告本次匹配到的商品",
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {"type": "string", "description":  "给用户的自然语言回复（语气与规则见系统提示）"},
                "current":{"type": "array", "items": {"type": "string"},
                           "description":
                                """匹配到的商品名称列表。
                                    - 名称照抄检索结果里的，不要概括或改写
                                    - 只填用户问到的，不要填你额外推荐的、举例提到的
                                    - 匹配不上（用户问的东西不在检索结果里）→ 返回空数组
                                    - 用户问了多个 → 返回多个"""
                           }
            },
            "required": ["answer","current"]
        }
    }
}]

def answer(query,history,doc = ''):
    messages = [
        {"role": "system", "content": ANSWER_PROMPT}
    ]
    working = history[-20:]
    if doc:
        working.append({"role": "user", "content": doc})
    messages.extend(working)
    logger.info("开始生成回复")
    messages.append({"role":"user","content":query})
    responses = call_llm(messages,answer_tool,{"type": "function", "function": {"name": "current_shop"}})
    tool_call = responses.choices[0].message.tool_calls[0]
    arguments = json.loads(tool_call.function.arguments)
    logger.info("生成回复内容为：%s ， 当前匹配商品为：%s",arguments["answer"],arguments["current"])
    return {"answer": arguments["answer"], "current": arguments["current"]}

