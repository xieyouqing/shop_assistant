import config
from retrieval.product_search import search_product
import logging
import json


logger = logging.getLogger(__name__)

tools = [
{
        "type":"function",
        "function":{
            "name":"search_product",
            "description":"查询商品库里的商品信息",
            "parameters":{
                "type":"object",
                "properties":{
                    "query":{"type":"string","description":"需要查询的商品信息"},
                },
                "required":["query"]
            },
        }
    }
]

TOOL_MAP ={
    "search_product":search_product
}

def execute_tool(tool_call):
    try:
        args = json.loads(tool_call.function.arguments)
        tool_name = tool_call.function.name
        fun = TOOL_MAP.get(tool_name)
        if fun is None:
            return f"错误，未知工具{tool_name}"
        logger.info("识别到工具： %s，参数： %s",tool_name,args)
        return fun(**args)

    except Exception as e:
        logger.error("工具执行失败，错误：%s", e)
        return f"工具执行失败，错误{e}"
