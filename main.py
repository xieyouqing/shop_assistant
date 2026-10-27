from agent.handle_turn import HandleTurn
import logging


logger = logging.getLogger(__name__)

# CLI 本来就是单用户：这个入口自己持有一份会话
session = HandleTurn()

def main():
    print("客服已上线，输入 exit 退出")
    while True:
        user_input = input("你：").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            break
        answer = session.handle_turn(user_input)
        print(f"客服：{answer}")

if __name__ == "__main__":
    main()
    print(history)
