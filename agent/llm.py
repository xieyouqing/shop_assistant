import config
import logging
from openai import OpenAI
import time


logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=config.DEEPSEEK_API_KEY,
    base_url=config.DEEPSEEK_BASE_URL
)

def call_llm(messages,tools=None,tool_choice=None,retry=1,tag=""):
    for i in range(retry+1):
        try:
            t0 = time.time()
            resp = client.chat.completions.create(
                model=config.DEEPSEEK_MODEL,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
            )
            logger.info("[用量] %s 输入=%d 输出=%d 耗时=%.2fs",
                        tag, resp.usage.prompt_tokens, resp.usage.completion_tokens, time.time() - t0)
            return resp
        except Exception as e:
            if i==retry:
                raise
            logger.error("调用失败，重试第 %d 次,%s",i+1,e)