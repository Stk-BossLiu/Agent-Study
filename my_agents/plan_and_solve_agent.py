"""
执行器
"""

# ==============================================================================#
EXECUTOR_PROMPT_TEMPLATE = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决“当前步骤”，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对“当前步骤”的回答:
"""
# ==============================================================================#
PLANNER_PROMPT_TEMPLATE = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题: {question}

请严格按照以下格式输出你的计划,```python与```作为前后缀是必要的:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""

from ast import List, literal_eval

import re

import os

from dotenv import load_dotenv

from main import HelloAgentsLLM

from main import HelloAgentsLLM

load_dotenv()


class Planner:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def plan(self, question: str) -> list[str]:
        """
        生成计划列表
        """
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        messages = [{"role": "user", "content": prompt}]
        print("========正在生成计划=========")
        response_text = self.llm_client.chat(messages=messages) or ""
        try:
            plan_list_str = re.search(
                r"```python\n(.*?)\n```", response_text, re.DOTALL
            ).group(1)
            plan: List = literal_eval(plan_list_str)
            return plan if isinstance(plan, list) else []

        except Exception as e:
            print(f"生成计划失败: {e}")
            return []


class Executor:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def execute_by_plan(self, question: str, plan: List[str]) -> str:
        if len(plan) == 0:
            print("计划为空， 执行结束")
            return ""
        history = []  # 历史步骤与结果
        print("\n========正在执行计划=========")
        for index, step in enumerate(plan):
            print(f"执行第{index + 1}步: {step}")
            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question, plan=plan, history=history, current_step=step
            )
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.chat(messages=messages) or ""
            # 更新历史记录
            history.append(f"步骤{index + 1}: {step}\n结果: {response_text}")
            print(f"步骤{index + 1}执行完成， 结果：{response_text}")

        ans = response_text
        return ans


class PlanAndSolveAgent:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.planner = Planner(llm_client)
        self.executor = Executor(llm_client)
        self.llm_client = llm_client

    def run(self, question: str) -> str:
        """
        先规划后执行
        """
        print(f"问题：{question}")
        plan = self.planner.plan(question)
        print(
            f"计划已生成: {'\n'.join(['步骤' + str(i + 1) + ': ' + step for i, step in enumerate(plan)])}"
        )
        ans = self.executor.execute_by_plan(question, plan)
        print(f"任务完成，最终回答：{ans}")


if __name__ == "__main__":
    llm_client = HelloAgentsLLM(
        model=os.getenv("LLM_MODEL_ID"),
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY"),
    )
    plan_and_solve_agent = PlanAndSolveAgent(llm_client)
    plan_and_solve_agent.run(input("请输入问题："))
