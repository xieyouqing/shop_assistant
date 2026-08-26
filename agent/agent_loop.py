import config
import logging
from openai import OpenAI
from agent.tools import tools,execute_tool


logger = logging.getLogger(__name__)

client = OpenAI(
    api_key= config.DEEPSEEK_API_KEY,
    base_url= config.DEEPSEEK_BASE_URL
)

def run_agent(messages:list,max_iterations:int=config.MAX_iterations):
    iterations = 0
    while iterations < max_iterations:
        iterations += 1
        try:
            responses = client.chat.completions.create(
                model= config.DEEPSEEK_MODEL,
                messages= messages,
                tools= tools,
                tool_choice= 'auto'
            )
            logger.info('已发送客户端请求')
        except Exception as e:
            logger.error(f"请求失败{e}")
            return f"请求失败{e}"
        assistant_msg = responses.choices[0].message
        if assistant_msg.tool_calls:
            bad_calls = [tc for tc in assistant_msg.tool_calls if not getattr(tc,'id',None)]
            if bad_calls:
                bad_name = bad_calls[0].function.name
                logger.error("模型返回了缺 id 的 tool_call，本轮作废：%s",bad_name)
                return f"模型返回了缺 id 的 tool_call，本轮作废：{bad_name}"
            messages.append(assistant_msg)
            for tool_call in assistant_msg.tool_calls:
                result = execute_tool(tool_call)
                messages.append({"role":"tool","tool_call_id":tool_call.id,"content":str(result)})
            continue
        else:
            return assistant_msg.content

    logger.error("超过最大执行次数 %d 仍未结束，本轮中止", max_iterations)
    return "抱歉，我这边处理遇到点困难，请稍后再试或换个问法"