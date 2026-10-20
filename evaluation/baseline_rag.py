# -*- coding: utf-8 -*-
"""
纯 RAG 对照臂 —— 故意的 naive 写法

它跟融合臂的差异，**只有**计划里定的那三个变量：
  ① 无路由       每轮都检索（闲聊也检索）
  ② 无 current   指代词不去替换，原句直接检索
  ③ 无两层历史   历轮的【检索结果】也塞进历史（naive RAG 的典型写法，也是污染源）

刻意保持**相同**的地方（不然对比就不公平）：
  · 同一个 LLM、同一个 ANSWER_PROMPT、同一个 answer()（连哑工具和输出格式都一样）
  · 历史窗口同样在 answer() 里切 [-20:]
    → 注意：naive 每轮往历史塞 3 条（问/答/检索结果），融合只塞 2 条，
      所以同样 20 条的窗口，naive 记的轮数更少。这不是 bug，是它自己要付的代价。
"""
from agent.prompt import ANSWER_PROMPT          # noqa: F401  （answer() 内部已用，这里显式标明用的是同一份）
from agent.answer import answer
from retrieval.product_search import search_product


class BaselineRAG:
    def __init__(self):
        self.history = []
        self.last_query = ""     # 给评估脚本记录证据用
        self.last_doc = ""       # 给 RAGAS 当 retrieved_contexts

    def reset(self):
        self.history.clear()
        self.last_query = ""
        self.last_doc = ""

    def handle_turn(self, query: str) -> str:
        self.last_query = query
        self.last_doc = doc = search_product(query)      # ①② 无条件检索 + 原句检索
        result = answer(query, self.history, doc)
        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": result["answer"]})
        self.history.append({"role": "user", "content": doc})   # ③ 检索结果也进历史
        return result["answer"]
