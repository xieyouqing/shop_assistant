import config
from openai import OpenAI
import logging
import json
from agent.prompt import QUERY_PROMPT,ROUTER_PROMPT


logger = logging.getLogger(__name__)

client = OpenAI(
    api_key= config.DEEPSEEK_API_KEY,
    base_url= config.DEEPSEEK_BASE_URL
)

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

rewrite_tools = [{
    "type": "function",
    "function": {
        "name": "rewrite_query",
        "description": "把指代性查询改写为自包含查询",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "改写后的查询"}
            },
            "required": ["query"]
        }
    }
}]

def router(query):
    messages = [
        {"role":"system","content":ROUTER_PROMPT},
        {"role":"user","content":query}
    ]
    try:
        logger.info("开始意图识别")
        resp = client.chat.completions.create(
            model= config.DEEPSEEK_MODEL,
            messages=messages,
            tools=tools,
            tool_choice={"type": "function","function":{"name":"route_to"}},
        )
        tool_call = resp.choices[0].message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)
        logger.info("意图识别成功,识别结果,route:%s,has_pronoun:%s",arguments["route"],arguments["has_pronoun"])
        return {"route" : arguments["route"],"has_pronoun":arguments["has_pronoun"]}
    except Exception as e:
        logger.error("意图识别环节出错 %s",e)
        return {"route":"product","has_pronoun":False}