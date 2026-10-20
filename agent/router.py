import config
import logging
import json
from agent.prompt import ROUTER_PROMPT
from agent.llm import call_llm


logger = logging.getLogger(__name__)

tools = [
{
        "type":"function",
        "function":{
            "name":"route_to",
            "description":"判断用户问题的意图（product/chat），并判断该问题是否依赖上文",
            "parameters":{
                "type":"object",
                "properties":{
                    "route":{
                        "type":"string",
                        "enum":["product","chat"],
                        "description":"问题意图判断结果"},
                    "has_pronoun": {"type": "boolean", "description":"用户的问题是否依赖上文才能理解（例如用'它/这款/那个'指代之前提过的商品）。只判断这句话本身的措辞，不需要考虑上文里是否真的有可指代的对象。"},
                },
                "required":["route","has_pronoun"]
            },
        }
    }
]


def router(query):
    messages = [
        {"role":"system","content":ROUTER_PROMPT},
        {"role":"user","content":query}
    ]
    try:
        logger.info("开始意图识别")
        resp = call_llm(messages,tools,{"type": "function","function":{"name":"route_to"}},tag="router")
        tool_call = resp.choices[0].message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)

        # 模型偶尔把 enum 返回成 ['product'] / False / "PRODUCT" 这类非字符串，必须校验并归一化
        raw_route = arguments.get("route")
        route = str(raw_route).strip().lower()
        if route not in ("product", "chat"):
            logger.warning("route 返回值非法，按 product 兜底：%r", raw_route)
            route = "product"

        # 必须是真 bool —— 字符串 "false" 是 truthy，直接用会导致误替换查询
        raw_pronoun = arguments.get("has_pronoun")
        if isinstance(raw_pronoun, bool):
            has_pronoun = raw_pronoun
        else:
            s = str(raw_pronoun).strip().lower()
            if s in ("true", "1"):
                has_pronoun = True
            elif s in ("false", "0"):
                has_pronoun = False
            else:
                logger.warning("has_pronoun 返回值非法，按 False 兜底：%r", raw_pronoun)
                has_pronoun = False

        logger.info("意图识别成功,识别结果,route:%s,has_pronoun:%s", route, has_pronoun)
        return {"route": route, "has_pronoun": has_pronoun}
    except Exception as e:
        logger.error("意图识别环节出错 %s",e)
        return {"route":"product","has_pronoun":False}