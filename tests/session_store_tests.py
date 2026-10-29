from agent.session_store import SessionStore
import threading
import time

passed = total = 0


def check(name, cond):
    global passed, total
    total += 1
    print(("✓" if cond else "✗"), name)
    if cond:
        passed += 1


store = SessionStore()

# 1. 不同 sid → 不同实例
a = store.get(111)
a1 = store.get(112)
check("1. 不同 sid → 不同实例", a is not a1)

# 2. 同一 sid 两次 get → 同一实例
b = store.get(222)
b1 = store.get(222)
check("2. 同一 sid 两次 get → 同一实例", b is b1)

# 3. drop 后再 get → 新实例
c = store.get(333)
store.drop(333)
c1 = store.get(333)
check("3. drop 后再 get → 新实例", c is not c1)

# 4. drop 不存在的 sid → 不报错
d = store.drop(444)
check("4. drop 不存在的 sid → 不报错", d is None)

# 5. 过期后再 get → 新实例（TTL 调小 + 等待，不用改时间）
s = SessionStore(ttl=0.1)
e = s.get(555)
time.sleep(0.3)
e1 = s.get(555)
check("5. 过期后重建", e is not e1)

# 6. 过期项真的从 dict 里删掉（用两个 sid 才看得出来）
s = SessionStore(ttl=0.1)
s.get("x")
s.get("y")
time.sleep(0.2)
s.get("z")  # 这次 get 会先触发 _sweep
check("6. 过期项被清掉", len(s._sessions) == 1)

# 7. TTL 边界：代码用 `>`，刚好等于 ttl 不算过期
#    真实时间测不到"刚好等于"，用白盒改 last_seen 测两侧
s = SessionStore(ttl=10)
f = s.get("f")
s._sessions["f"] = (f, time.time() - 9)     # 差 1 秒到期
check("7a. 未到 ttl 不过期", s.get("f") is f)

s._sessions["f"] = (f, time.time() - 11)    # 超过 1 秒
check("7b. 超过 ttl 过期", s.get("f") is not f)

# 8. 两个线程同时 get 同一个新 sid → 只有一个实例
#    注意：这是冒烟测试，不是严格证明（GIL 下可能碰不到真的交错）
s = SessionStore()
results = []
barrier = threading.Barrier(2)


def worker():
    barrier.wait()  # 两个线程卡在同一起点，增大并发概率
    results.append(s.get("same"))


threads = [threading.Thread(target=worker) for _ in range(2)]
for t in threads:
    t.start()
for t in threads:
    t.join()
check("8. 并发同 sid 只有一个实例", results[0] is results[1])

print(f"\n{passed}/{total}")
