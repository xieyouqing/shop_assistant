import logging
import config
from openai import OpenAI
from agent.prompt import ANSWER_PROMPT


client = OpenAI(
    api_key=config.DEEPSEEK_API_KEY,
    base_url=config.DEEPSEEK_BASE_URL
)

logger = logging.getLogger(__name__)

def answer(query,history,doc = ''):
    messages = [
        {"role": "system", "content": ANSWER_PROMPT}
    ]
    working = history.copy()
    if doc:
        working.append({"role": "user", "content": doc})
    messages.extend(working)
    try:
        logger.info("开始生成回复")
        messages.append({"role":"user","content":query})
        responses = client.chat.completions.create(
            model=config.DEEPSEEK_MODEL,
            messages=messages,
        )
        result = responses.choices[0].message.content
        logger.info("生成回复内容为：%s",result)
        return result
    except Exception as e:
        logger.error("生成回复失败 %s",e)
        return "网络错误，请重新输入"