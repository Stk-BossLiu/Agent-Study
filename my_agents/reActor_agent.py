from datetime import datetime
from main import HelloAgentsLLM

from tools.main import ToolExcutor
import re
import os

from dotenv import load_dotenv

from tools.search import description, search

load_dotenv()


REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下:
{tools}

当前北京时间:
{time}

请严格按照以下格式进行回应:

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一:
- `{{tool_name}}[{{tool_input}}]`:调用一个可用工具。
- `Finish[最终答案]`:当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在Action:字段后使用 Finish[最终答案] 来输出最终答案。

现在，请开始解决以下问题:
Question: {question}
History: {history}
"""


class ReActAgent:
    def __init__(
        self, llm_client: HelloAgentsLLM, tool_executor: ToolExcutor, max_steps: int = 5
    ):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def run(self, question: str) -> str:
        self.history = []  # 重置历史对话记录
        current_step = 0
        while current_step < self.max_steps:
            current_step += 1
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=self.tool_executor.getAvailableTools(),
                time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                question=question,
                history="\n".join(self.history),
            )
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.chat(messages=messages)
            thought, action = self._parseOutput(response_text)
            if thought:
                print(f"Thought: {thought}")
            if not action:
                print("没有action")
                break
            if action.startswith("Finish"):
                # Finish -> 最终答案
                final_ans = re.match(r"Finish\[(.*)\]", action, re.DOTALL).group(1)
                print(f"最终答案: {final_ans}")
                return final_ans
            tool_name, tool_input = self._parseAction(action)
            tool_function = self.tool_executor.getTool(tool_name)
            tool_result = tool_function(tool_input)
            if tool_result:
                self.history.append(f"Action: {action}\n Result: {tool_result}")
        return None

    def _parseOutput(self, text: str) -> str:
        # Thought:-> Action
        thought_match = re.search(
            r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL
        )  # DOTALL 表示.匹配任意字符，包括换行符
        # Action:-> end
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parseAction(self, action_text: str) -> str:
        action_parts = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        if action_parts:
            return action_parts.group(1), action_parts.group(2)
        return None, None


if __name__ == "__main__":
    llm_client = HelloAgentsLLM(
        model=os.getenv("LLM_MODEL_ID"),
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY"),
    )
    tool_executor = ToolExcutor()
    tool_executor.registerTool("Search", description, search)
    react_agent = ReActAgent(llm_client, tool_executor, 10)
    question = input("请输入问题: ")
    react_agent.run(question)
