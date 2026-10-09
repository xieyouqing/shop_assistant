from agent.handle_turn import history

history.clear()
for i in range(15):                      # 塞 15 组 = 30 条
    history.append({"role":"user","content":f"q{i}"})
    history.append({"role":"assistant","content":f"a{i}"})

print(len(history))         # 30
print(len(history[-20:]))   # 是否 20 ✓
print(history[-20:][0])     # 第一条是 user 还是 assistant？ ← 关键