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
            "description":"判断用户问题意图：涉及商品/购物/售后时输出 product; 纯闲聊输出 chat",
            "parameters":{
                "type":"object",
                "properties":{
                    "route":{
                        "type":"string",
                        "enum":["product","chat"],
                        "description":"判断结果"},
                },
                "required":["route"]
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
        logger.info("意图识别成功,识别结果：%s",arguments["route"])
        return arguments["route"]
    except Exception as e:
        logger.error("意图识别环节出错 %s",e)
        return "product"


def rewrite(query, history) -> str:
    messages =[
        {"role": "system", "content": QUERY_PROMPT},
        {"role": "user", "content": history}
    ]
    query_1 = f"[问题]{query}"
    messages.append({"role":"user","content":query_1})
    try:
        logger.info("开始查询改写，用户输入内容：%s",query)
        responses = client.chat.completions.create(
            model=config.DEEPSEEK_MODEL,
            messages=messages,
            tools=rewrite_tools,
            tool_choice={"type": "function", "function": {"name": "rewrite_query"}}
        )

        tool_call = responses.choices[0].message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)
        logger.info("查询改写结果:%s",arguments["query"])
        return arguments["query"]
    except Exception as e:
        logger.error("查询改写失败，返回原问题，错误：%s",e)
        return query