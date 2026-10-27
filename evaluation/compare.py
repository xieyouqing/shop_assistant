# -*- coding: utf-8 -*-
"""
④ 评估对比：纯RAG  vs  融合工作流

跑法（必须用项目自带的解释器，不然 import 不到 langchain_core）：
    .\\.venv\\Scripts\\python.exe -m evaluation.compare                # 两套都跑
    .\\.venv\\Scripts\\python.exe -m evaluation.compare --arm fused    # 只跑一套
    .\\.venv\\Scripts\\python.exe -m evaluation.compare --limit 3      # 冒烟：只跑前 3 条
    .\\.venv\\Scripts\\python.exe -m evaluation.compare --ragas        # 额外跑 RAGAS（需先装 ragas）

产物（这些 JSON 就是写结论的证据，别只贴结论不贴数据）：
    evaluation/result_baseline.json / result_fused.json / result_ragas.json

两层判据：
  A 层（默认，免费、确定、立刻能跑）—— 关键词硬判据，读 cases.py 里的 must / must_not
  B 层（--ragas，要装包 + 要你写参考答案）—— RAGAS Faithfulness + AnswerCorrectness
  A 层是主判据：'它多少钱' 该答 299 还是 1299，是业务事实，不需要再请个模型来判。
  B 层只补一个维度：回答有没有脱离检索结果（幻觉）。
"""
import argparse
import json
import logging
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.cases import all_cases          # noqa: E402
from evaluation.baseline_rag import BaselineRAG  # noqa: E402
import agent.handle_turn as ht                   # noqa: E402
from agent.handle_turn import HandleTurn         # noqa: E402


# 单价（元 / 百万 token）—— 按你实际用的档位自己填，我不替你猜
PRICE_IN = None
PRICE_OUT = None

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ── token 计量：挂个 handler 在 agent.llm 上，正则捞它自己打的那行用量日志 ──
class TokenMeter(logging.Handler):
    _PAT = re.compile(r"输入=(\d+) 输出=(\d+) 耗时=([\d.]+)")

    def __init__(self):
        super().__init__(level=logging.INFO)
        self.prompt = self.completion = self.calls = 0
        self.seconds = 0.0

    def emit(self, record):
        m = self._PAT.search(record.getMessage())
        if not m:
            return
        self.prompt += int(m.group(1))
        self.completion += int(m.group(2))
        self.seconds += float(m.group(3))
        self.calls += 1


# ── 两条臂：turn(query)->str / reset() / evidence()->(检索词, 检索结果) ──
_REC = {"检索词": "", "检索结果": ""}


def make_fused():
    session = HandleTurn()
    real_search = ht.search_product

    def recording_search(q):
        doc = real_search(q)
        _REC["检索词"] = q
        _REC["检索结果"] = doc
        return doc

    ht.search_product = recording_search      # 只改运行时，不动你的源码

    def turn(q):
        _REC["检索词"] = _REC["检索结果"] = ""   # 闲聊分支不检索，不清就跟留上一轮的
        return session.handle_turn(q)

    def reset():
        session.history.clear()
        session.current = []

    return turn, reset, (lambda: (_REC["检索词"], _REC["检索结果"]))


def make_baseline():
    b = BaselineRAG()
    return b.handle_turn, b.reset, (lambda: (b.last_query, b.last_doc))


def run_arm(name, arm, cases):
    turn, reset, evidence = arm
    meter = TokenMeter()
    lg = logging.getLogger("agent.llm")
    lg.addHandler(meter)
    rows, t0 = [], time.time()
    try:
        for i, c in enumerate(cases, 1):
            reset()
            replies, ev = [], []
            for q in c["轮次"]:
                _REC.update({"检索词": "", "检索结果": ""})
                try:
                    r = turn(q)
                except Exception as e:
                    r = f"[异常] {type(e).__name__}: {e}"
                replies.append(r)
                ev.append({"检索词": evidence()[0], "检索结果": evidence()[1]})
            ok, why = judge({**c, "末轮": replies[-1]})
            rows.append({**c, "回复": replies, "检索": ev, "末轮": replies[-1],
                         "通过": ok, "原因": why})
            print(f"  [{i}/{len(cases)}] {c['id']:<3} {'✓' if ok else '✗ ' + why}")
    finally:
        lg.removeHandler(meter)
    cost = None
    if PRICE_IN is not None and PRICE_OUT is not None:
        cost = round(meter.prompt / 1e6 * PRICE_IN + meter.completion / 1e6 * PRICE_OUT, 4)
    stat = {"臂": name, "调用次数": meter.calls, "输入token": meter.prompt,
            "输出token": meter.completion, "模型耗时秒": round(meter.seconds, 1),
            "墙钟秒": round(time.time() - t0, 1), "成本元": cost,
            "通过": sum(r["通过"] for r in rows), "总数": len(rows)}
    return rows, stat


_WS = re.compile(r"\s+")


def hit(kw, text):
    """
    关键词命中判定。三条规则都是被真实误判逼出来的，不是想当然加的：
      ① 去掉所有空白再比 —— 模型会写 '40 小时'，而判据写的是 '40小时'
      ② 纯数字卡数字边界 —— '299' 不能被 '1299' 命中（T2 踩过这个坑）
      ③ kw 写成列表 = 或关系 —— 提示词明确允许两种说法时（'人工' 或 '公告'）
    """
    text = _WS.sub("", text)
    if isinstance(kw, (list, tuple)):
        return any(hit(k, text) for k in kw)
    kw = _WS.sub("", kw)
    if kw.isdigit():
        return re.search(rf"(?<!\d){re.escape(kw)}(?!\d)", text) is not None
    return kw in text


def _label(kw):
    return "或".join(kw) if isinstance(kw, (list, tuple)) else kw


def judge(row):
    t = row["末轮"]
    miss = [w for w in row["must"] if not hit(w, t)]
    dirty = [w for w in row["must_not"] if hit(w, t)]
    why = ""
    if miss:
        why += "缺" + "/".join(_label(w) for w in miss)
    if dirty:
        why += ("·" if why else "") + "混入" + "/".join(_label(w) for w in dirty)
    return (not miss and not dirty), why


def brief(s, n=220):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n] + "…"


def report(rows_by_arm, stats):
    print("\n" + "=" * 68)
    print("汇总")
    print("=" * 68)
    for k, v in stats.items():
        cost = f"  ≈{v['成本元']}元" if v["成本元"] is not None else ""
        print(f"{v['臂']:<8} 通过 {v['通过']}/{v['总数']}   "
              f"调用 {v['调用次数']} 次   token {v['输入token']}→{v['输出token']}{cost}")
    print()
    ids = [r["id"] for r in next(iter(rows_by_arm.values()))]
    names = list(rows_by_arm)
    print("逐条：")
    print(f"  {'id':<4}{'类别':<20}" + "".join(f"{n:<12}" for n in names))
    by_arm = {n: {r["id"]: r for r in rows_by_arm[n]} for n in names}
    for cid in ids:
        cat = by_arm[names[0]][cid]["类别"]
        cells = "".join(f"{('✓' if by_arm[n][cid]['通过'] else '✗ ' + by_arm[n][cid]['原因']):<12}"
                        for n in names)
        print(f"  {cid:<4}{cat:<20}{cells}")

    multi = [cid for cid in ids if len(by_arm[names[0]][cid]["轮次"]) > 1]
    print("\n" + "=" * 68)
    print("多轮用例明细（这三个变量的效果都在这 6 条里）")
    print("=" * 68)
    for cid in multi:
        c0 = by_arm[names[0]][cid]
        print(f"\n--- {cid} {c0['类别']} ---")
        print(f"  轮次: {' → '.join(c0['轮次'])}")
        print(f"  判据: must={c0['must']}  must_not={c0['must_not']}")
        if c0["要点"]:
            print(f"  要点: {c0['要点']}")
        for n in names:
            r = by_arm[n][cid]
            print(f"  [{n}] {'✓ 通过' if r['通过'] else '✗ ' + r['原因']}")
            print(f"     检索词: " + " | ".join(brief(e["检索词"], 40) or "(未检索)" for e in r["检索"]))
            print(f"     末轮回复: {brief(r['末轮'])}")


def run_ragas(rows_by_arm):
    """B 层：需要 pip install ragas。只对有检索结果的轮次算。"""
    try:
        import config
        from ragas import evaluate, EvaluationDataset, SingleTurnSample
        from ragas.metrics import Faithfulness, AnswerCorrectness
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings.base import LangchainEmbeddingsWrapper
        from langchain_openai import ChatOpenAI
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError as e:
        print(f"\n[跳过 RAGAS] 缺依赖：{e}\n  装：.\\.venv\\Scripts\\python.exe -m pip install ragas langchain-openai")
        return None

    llm = LangchainLLMWrapper(ChatOpenAI(model=config.DEEPSEEK_MODEL,
                                         api_key=config.DEEPSEEK_API_KEY,
                                         base_url=config.DEEPSEEK_BASE_URL))
    emb = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL_NAME,
        cache_folder=str(config.HF_HOME),
        model_kwargs={"device": "cpu"}))

    out = {}
    for name, rows in rows_by_arm.items():
        samples, need_ref = [], False
        for r in rows:
            ctx = r["检索"][-1]["检索结果"]
            if not ctx:
                continue                      # 没检索就没 context，Faithfulness 无从谈起
            if not r["参考"]:
                need_ref = True
            samples.append(SingleTurnSample(
                user_input=r["轮次"][-1],
                response=r["末轮"],
                retrieved_contexts=[ctx],
                reference=r["参考"] or None))
        if not samples:
            print(f"[跳过 RAGAS] {name}: 没有带检索结果的样本")
            continue
        metrics = [Faithfulness()]
        if not need_ref:
            metrics.append(AnswerCorrectness())
        else:
            print(f"[提示] {name}: cases.py 里还有用例的『参考』是空的，已跳过 AnswerCorrectness")
        res = evaluate(dataset=EvaluationDataset(samples=samples), metrics=metrics,
                       llm=llm, embeddings=emb)
        out[name] = {"样本数": len(samples),
                     **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()
                        if not isinstance(v, list)}}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["baseline", "fused", "both"], default="both")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 条（冒烟用）")
    ap.add_argument("--id", default="", help="只跑指定 id，逗号分隔，如 --id T1,T2")
    ap.add_argument("--ragas", action="store_true", help="额外跑 RAGAS（需先装包）")
    a = ap.parse_args()

    if a.id:
        want = {s.strip() for s in a.id.split(",") if s.strip()}
        cases = [c for c in all_cases if c["id"] in want]
    else:
        cases = all_cases[:a.limit] if a.limit else all_cases
    todo = {"baseline": [("纯RAG", make_baseline)],
            "fused": [("融合", make_fused)],
            "both": [("纯RAG", make_baseline), ("融合", make_fused)]}[a.arm]

    rows_by_arm, stats = {}, {}
    for name, factory in todo:
        print(f"\n=== 跑 {name}（{len(cases)} 条）===")
        rows, st = run_arm(name, factory(), cases)
        rows_by_arm[name], stats[name] = rows, st
        # 用 --id / --limit 时不覆盖全量结果，避免"跑一条就把证据冲掉"
        suffix = f"_{a.id.replace(',', '-')}" if a.id else (f"_limit{a.limit}" if a.limit else "")
        p = os.path.join(OUT_DIR, f"result_{'baseline' if name == '纯RAG' else 'fused'}{suffix}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"统计": st, "明细": rows}, f, ensure_ascii=False, indent=2)
        print(f"  → {p}")

    report(rows_by_arm, stats)

    if a.ragas:
        r = run_ragas(rows_by_arm)
        if r:
            print("\n=== RAGAS ===")
            for k, v in r.items():
                print(f"  {k}: {v}")
            with open(os.path.join(OUT_DIR, "result_ragas.json"), "w", encoding="utf-8") as f:
                json.dump(r, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
