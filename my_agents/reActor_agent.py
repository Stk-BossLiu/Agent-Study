from datetime import datetime
import json
from main import HelloAgentsLLM

from tools import caculator
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
{{
    "Thought": "你的思考过程，用于分析问题、拆解任务和规划下一步行动。",
    "Action": {{
        "isFinish": bool,
        "result": str,
        "toolName": str,
        "toolInput": str,
    }}
}}

Action中各字段解释
- isFinish: 是否已经获得最终答案
- result: 执行结果
- toolName: 工具名称
- toolInput: 工具输入
- 当你收集到足够的信息，isFinish为True。
- 如果没有使用工具，toolName为空，toolInput为空。

涉及到需要数学计算时，必须优先调用工具以获得更加精确的结果。

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

            if action["isFinish"]:
                # Finish -> 最终答案
                final_ans = action["result"]
                print(f"最终答案: {final_ans}")
                return final_ans
            tool_name, tool_input = action["toolName"], action["toolInput"]
            tool_function = self.tool_executor.getTool(tool_name) or ""
            tool_result = tool_function(tool_input) or ""
            if tool_result:
                self.history.append(f"Action: {action}\n Result: {tool_result}")
        return None

    def _parseOutput(self, text: str) -> str:
        # Thought:-> Action
        data = json.loads(text)
        thought = data.get("Thought")
        action = data.get("Action")
        return thought, action


if __name__ == "__main__":
    llm_client = HelloAgentsLLM(
        model=os.getenv("LLM_MODEL_ID"),
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY"),
    )
    tool_executor = ToolExcutor()
    tool_executor.registerTool("Search", description, search)
    tool_executor.registerTool("Caculator", description, caculator.caculate)
    react_agent = ReActAgent(llm_client, tool_executor, 10)
    question = input("请输入问题: ")
    react_agent.run(question)
