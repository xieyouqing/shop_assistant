import config
import logging
from openai import OpenAI


logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=config.DEEPSEEK_API_KEY,
    base_url=config.DEEPSEEK_BASE_URL
)

def call_llm(messages,tools=None,tool_choice=None,retry=1):
    for i in range(retry+1):
        try:
            return client.chat.completions.create(
                model=config.DEEPSEEK_MODEL,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
            )
        except Exception as e:
            if i==retry:
                raise
            logger.error("调用失败，重试第 %d 次,%s",i+1,e)