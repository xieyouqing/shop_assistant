from agent.handle_turn import handle_turn,history
import logging


logger = logging.getLogger(__name__)

def main():
    print("客服已上线，输入 exit 退出")
    while True:
        user_input = input("你：").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            break
        answer = handle_turn(user_input)
        print(f"客服：{answer}")

if __name__ == "__main__":
    main()
    print(history)