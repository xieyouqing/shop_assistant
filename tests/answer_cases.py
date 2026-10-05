from agent.handle_turn import handle_turn,history,current


# (类别, 输入, 历史, must 必含词, must_not 不该含词)
cases = [
 # ── 库内商品 ──
 ("库内", "你们有耳机吗", [],        ["AirPro"], []),
 ("库内", "手机多少钱", [],          ["3999"], []),
 ("库内", "充电宝有现货吗", [],       ["300"], []),
 ("库内", "手表续航多久", [],        ["14"], []),
 ("库内", "笔记本什么配置", [],       ["AirBook"], []),

 # ── 库外商品（关键：不许推别的商品凑答案）──
 ("库外", "你们有卖冰箱吗", [],      ["没有"], ["AirPro", "星耀", "FitWatch"]),
 ("库外", "有卖小汽车吗", [],        ["没有"], ["AirPro", "星耀", "FitWatch"]),
 ("库外", "有空调吗", [],            ["没有"], ["AirPro", "星耀", "FitWatch"]),

 # ── 属性查询（该筛出多个）──
 ("属性", "有没有防水的", [],        ["IPX5", "5ATM"], []),
 ("属性", "续航长的有哪些", [],       ["AirPro", "FitWatch"], []),
 ("属性", "有降噪的吗", [],          ["AirPro"], []),

 # ── 多对象 ──
 ("多对象", "有耳机和手表吗", [],     ["AirPro", "FitWatch"], []),
 ("多对象", "有手机和冰箱吗", [],     ["星耀", "没有"], []),
 ("多对象", "手机和耳机哪个好", [],   ["星耀", "AirPro"], []),

 # ── 同义词（要能归一化到库内商品）──
 ("同义词", "有移动电源吗", [],      ["充电宝"], []),
 ("同义词", "笔记本电脑多少钱", [],   ["AirBook"], []),
 ("同义词", "手环有吗", [],          ["FitWatch"], []),

 # ── 政策 / 闲聊 ──
 ("政策", "可以7天无理由退货吗", [],  ["人工", "公告"], []),
 ("闲聊", "你好呀", [],              [], ["AirPro", "299"]),
 ("闲聊", "今天天气怎么样", [],       [], ["AirPro", "299"]),
]

cases_1 = [
"你们有卖冰箱吗",
"有卖小汽车吗",
"有空调吗"
]

if __name__ == '__main__':
    a = []
    for i in range(len(cases)):
        history.clear()
        current.clear()
        must = cases[i][3]
        must_not = cases[i][4]
        history = cases[i][2]
        query = cases[i][1]
        reply = handle_turn(query)
        result = all(w in reply for w in must) and not any(w in reply for w in must_not)
        if result:
            a.append(["通过",f"{i+1}/{len(cases)}"])
        else:
            a.append(["失败",f"{i+1}/{len(cases)}"])

    b = []

    for x in range(len(cases_1)):
        history.clear()
        current.clear()
        result = handle_turn(cases_1[x])
        b.append(result)

    # ② 指代单独跑（真·两轮）
    history.clear(); current.clear()
    handle_turn("有耳机吗")          # ← 这一轮更新 current
    r2 = handle_turn("它多少钱")      # ← 这一轮用 current
    print("指代:", "通过" if "AirPro" in r2 else "失败", r2[:60])


    for j in a:
        print(j)

    for y in b:
        print(y)