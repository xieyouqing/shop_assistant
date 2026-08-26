import config
from agent.agent_loop import run_agent
from agent.prompt import SYSTEM_PROMPT
import logging


logger = logging.getLogger(__name__)

def main():
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("客服已上线，输入 exit 退出")
    while True:
        user_input = input("你：").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            break
        history.append({"role": "user", "content": user_input})
        working = history.copy()
        answer = run_agent(working)
        history.append({"role": "assistant", "content": answer})
        print(f"客服：{answer}")

if __name__ == "__main__":
    main()