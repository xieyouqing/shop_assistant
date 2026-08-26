# 数码 3C 电商客服 Agent 1.0
基于RAG+Agent手写循环的智能客服，能实现商品库查询

## 技术栈
Python / DeepSeek / FAISS 向量检索 / BM25 + jieba 中文分词 / RRF 融合 / 手写 Agent 循环

## 架构
```
 用户输入
    |
    v
  main.py (拼 messages / 打印客服回答)
    |
    v
  agent_loop (循环调 DeepSeek，最多5轮)
    |
    |--- 有 tool_calls ───────────┐
    |                             v
    |                      execute_tool
    |                             |
    |                             v
    |                     search_product(query)
    |                             |
    |                             v
    |                 hybrid_retriever.search(query)
    |                             |
    |                  +----------+----------+
    |                  |                     |
    |                  v                     v
    |             vector (FAISS)     bm25 (jieba)
    |                  |                     |
    |                  +----------+----------+
    |                             |
    |                             v
    |                      RRF 融合 1/(k+rank)
    |                             |
    |                             v
    |                     取 top5 (HYBRID_TOP_N)
    |                             |
    |                             v
    |                product_search 格式化 + 关键词兜底
    |                             |
    |<------------ tool 结果塞回 messages ----┘
    |
    v
  客服回答 (无 tool_calls)
```

## 目录结构
```
  shop_assistant/
  ├── config.py                  # 项目配置文件
  ├── main.py                    # 主程序入口
  ├── requirements.txt           # 软件包版本声明
  ├── .env.example               # 环境变量模板（.env 含真实 key，不提交）
  ├── data/
  │   └── products.json          # 商品信息存储文件
  ├── indexing/
  │   ├── __init__.py            # 包标记
  │   ├── product_loader.py      # 读取商品库信息
  │   └── build_index.py         # 创建商品信息向量库
  ├── retrieval/
  │   ├── __init__.py            # 包标记
  │   ├── vector_retriever.py    # FAISS向量检索
  │   ├── bm25_retriever.py      # bm25检索
  │   ├── hybrid_retriever.py    # 混合检索，两路检索结果 RRF 融合
  │   └── product_search.py      # 对外唯一接口：格式化+未找到兜底
  ├── agent/
  │   ├── __init__.py            # 包标记
  │   ├── tools.py               # 工具 schema + TOOL_MAP + execute_tool
  │   ├── agent_loop.py          # 手写 ReAct 循环
  │   └── prompt.py              # Agent提示词
  ├── reranker.py                # 重排预留，v1 关闭
  ├── FAISS_INDEX/               # 生成的索引（.gitignore 排除）
  └── logs/                      # 运行日志（.gitignore 排除）
```

## 运行方式
1. 装依赖：pip install -r requirements.txt
2. 建索引：python -m indexing.build_index
3. 启动客服：python main.py

## 演示场景
- 问价格 → 自动查库答价格库存
- 查不到 → 如实说没有，不编造
- 用户闲聊 → 直接答不调工具

## 后续计划
路由① / 记忆② / 兜底③ / 部署上云