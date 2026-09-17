cases = [
    ("你们有耳机吗", "product", "问商品"),
    ("你好呀",      "chat",    "纯寒暄"),
    ("你们这里有冰箱吗", "product","问商品"),
    ("你们可以7天无理由退货吗", "product", "问政策"),
    ("推荐几款有性价比的手机给我", "product", "问商品"),
    ("今天天气怎么样", "chat",    "纯寒暄"),
    ("你们的耳机保修多久啊", "product", "问商品"),
    ("他要多少钱啊", "product", "含指代/信息不足 → 靠意图信号+兜底偏置判"),
    ("现在几点了", "chat",    "非业务的事实提问"),
    ("我现在预算有限，你觉得我是买机好还是买手表好", "product", "问商品"),
    ("现在几点了？你们这里的耳机贵不贵", "product", "混合"),
    ("我失恋了，你安慰一下我", "chat",    "情绪倾诉"),
    ("怎么申请退款啊", "product", "无商品词的业务问题"),
    ("我下单的耳机什么时候能到啊", "product", "问物流"),
    ("现在买耳机有什么有什么优惠呀", "product", "问优惠")
]

from agent.router import router

list_1 = []

for i in cases:
    result = router(i[0])
    if result == i[1]:
        list_1.append(f"问题：{i[0],}，预测结果：{i[1]}，返回结果{result}，通过")
    else:
        list_1.append(f"问题：{i[0],}，预测结果：{i[1]}，返回结果{result}，失败")
for a in list_1:
    print(a)