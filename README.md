# 数码 3C 电商客服 Agent

基于 RAG + 工作流的智能客服：意图分流、商品检索、多轮指代、分层兜底。

## 技术栈

Python 3.10 / DeepSeek / FAISS 向量检索 / BM25 + jieba 中文分词 / RRF 融合 / 工作流编排 / 哑工具（`tool_choice` 锁定输出）

## 架构

```
用户输入
  │
  ▼
main.py
  │
  ▼
agent/handle_turn.py                 编排 + 整轮兜底
  │
  ├─► agent/router.py                哑工具：route(product/chat) + has_pronoun
  │     ├─ product
  │     │    ├─ 有指代且 current 非空 → 用 current 替换查询
  │     │    └─ search_product(query)
  │     │          └─ retrieval/hybrid_retriever.py
  │     │                ├─ vector (FAISS)
  │     │                ├─ bm25 (jieba)
  │     │                ├─ RRF 融合
  │     │                └─ 型号精确匹配置顶
  │     │          → 取 top5 → 格式化
  │     └─ chat                   不检索
  │
  └─► agent/answer.py                哑工具：answer + current（本轮匹配到的商品）
  │
  ▼
写两层历史（自然对话持久，检索结果用完即弃）+ 更新 current
  │
  ▼
客服回复
```

**三层兜底**

1. router 异常或返回值非法 → 强制走 product（宁可多查一次，不能漏查）
2. 检索异常 / 向量库不可用 → 自动降级为 BM25-only
3. 整轮异常 → 返回人话「网络错误，请重新输入」

## 目录结构

```
shop_assistant/
├── config.py
├── main.py                      命令行入口
├── api.py                       HTTP 接口（FastAPI）
├── requirements.txt
├── requirements.lock            锁定依赖版本，用于服务器复现
├── .env.example
├── data/
│   ├── products.json            商品库（45 SKU）
│   ├── products_5.json          旧 5 SKU 快照（对照实验用）
│   └── products_45.json         与 products.json 内容相同（可删）
├── indexing/
│   ├── product_loader.py
│   └── build_index.py
├── retrieval/
│   ├── vector_retriever.py
│   ├── bm25_retriever.py
│   ├── hybrid_retriever.py      RRF + 型号精确匹配置顶
│   └── product_search.py        对外唯一接口：格式化 + 未找到兜底
├── agent/
│   ├── router.py                意图识别 + 指代判断（哑工具）
│   ├── answer.py                生成回复 + 报告 current（哑工具）
│   ├── handle_turn.py           编排 + 两层历史 + 兜底
│   ├── llm.py                   公共调用（重试 + 用量日志）
│   └── prompt.py
├── evaluation/
│   ├── README.md                对照实验结论
│   ├── cases.py                 27 条用例
│   ├── baseline_rag.py          纯 RAG 对照臂
│   └── compare.py               两套对照 + 判据 + token 计量
├── tests/
│   ├── router_tests.py
│   ├── answer_cases.py
│   └── history_tests.py
├── FAISS_INDEX/                 生成，gitignore
└── logs/                        生成，gitignore
```

## 运行方式

```powershell
# 1. 依赖
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

# 2. 环境变量
copy .env.example .env            # 填入 DEEPSEEK_API_KEY

# 3. 建索引（首次 / 换库后）
.\.venv\Scripts\python.exe -m indexing.build_index

# 4. 启动（命令行）
.\.venv\Scripts\python.exe main.py
```

## HTTP 接口

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --host 0.0.0.0 --port 8000
```

| 接口 | 说明 |
|---|---|
| `POST /chat` | `{"query": "..."}` → `{"answer": "..."}` |
| `GET /health` | 健康检查 |
| `POST /reset` | 清空会话状态（单用户 demo：`history` / `current` 是进程内全局） |

启动后可访问 `/docs` 使用自动生成的接口调试页。

## 评估

两套对照（纯 RAG vs 融合工作流），27 条用例：

- **短对话 26 条**：26 : 26 打平
- **长对话 T7**（重复 5 次）：融合 **5/5**，纯 RAG **0/5**

结论是**有条件**的：融合的优势只在长对话 / 闲聊占比高时显现；短对话里它更贵（调用 2×）。

详见 [evaluation/README.md](evaluation/README.md)。复现：

```powershell
.\.venv\Scripts\python.exe -m evaluation.compare
```

## 演示场景

- 问价格 / 库存 / 规格 → 查库后回答
- 多轮指代（「有 AirPro 吗」→「它多少钱」）→ 用 `current` 解析
- 商品库没有的东西 → 如实说没有，不拿别的商品凑
- 闲聊 → 不检索，直接回复
- 政策问题 → 不编条款，建议人工确认

## 已知局限

- 多候选歧义：「你们有耳机吗 → 它多少钱」时两套都会猜一个、不反问（方案已定，未实现）
- 型号简称（`星耀 X5` 而非完整名）不触发精确匹配
- 关键词判据可能误伤「排除式表述」（详见 evaluation/README.md 第 7 节）

## 后续计划

- 部署上云（11 月中下）
