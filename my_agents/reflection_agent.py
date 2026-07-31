# ======================================================================================== #
INITIAL_PROMPT_TEMPLATE = """
你是一位精通所有编程语言的全栈开发工程师。请根据以下要求，使用规定语言编写一个函数。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。

语言: {language}
要求: {task}

请直接输出代码，不要包含任何额外的解释。
"""

# ======================================================================================== #
REFLECT_PROMPT_TEMPLATE = """
你是一位极其严格的代码评审专家和资深算法工程师，对代码的性能有极致的要求。
你的任务是审查以下代码，并专注于找出其在<strong>算法效率</strong>上的主要瓶颈。

原始任务:
{task}

待审查的代码:
```{language}
{code}
```

请分析该代码的时间复杂度，并思考是否存在一种<strong>算法上更优</strong>的解决方案来显著提升性能。
如果存在，请清晰地指出当前算法的不足，并提出具体的、可行的改进算法建议（例如，使用筛法替代试除法）。
如果代码在算法层面已经达到最优，才能回答“无需改进”。

请直接输出你的反馈，不要包含任何额外的解释。
"""

# ======================================================================================== #
REFINE_PROMPT_TEMPLATE = """
你是一位精通所有编程语言的算法专家。你正在根据一位代码评审专家的反馈来优化你的代码。

# 原始任务:
{task}

# 你上一轮尝试的代码:
{last_code_attempt}
评审员的反馈：
{feedback}

请根据评审员的反馈，生成一个优化后的新版本代码。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。
请直接输出优化后的代码，不要包含任何额外的解释。
"""
# ======================================================================================== #

from main import HelloAgentsLLM
from enum import Enum

from memory.easily_memory import EasilyMemory

from dotenv import load_dotenv

import os

load_dotenv()


class Language(Enum):
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    RUBY = "ruby"
    PHP = "php"
    C = "c"
    CPP = "cpp"
    CSHARP = "csharp"


# 执行 -> 反思 -> 优化 -> 反思 -> ...
class ReflectionAgent:
    def __init__(self, llm_client: HelloAgentsLLM, max_iterations: int = 3):
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.memory = EasilyMemory()

    def run(self, task: str, language: Language) -> str:
        iteration = 0
        initial_prompt = INITIAL_PROMPT_TEMPLATE.format(
            language=language.value, task=task
        )
        initial_messages = [{"role": "user", "content": initial_prompt}]
        initial_response = self.llm_client.chat(initial_messages) or ""
        self.memory.add_record("execution", initial_response)
        while iteration < self.max_iterations:
            print(f"===============第{iteration}轮迭代=================")
            iteration += 1
            last_execution = self.memory.get_last_execution()
            if last_execution is None:
                print("没有找到执行记忆，程序结束")
                break
            reflection_prompt = REFLECT_PROMPT_TEMPLATE.format(
                task=task, code=last_execution, language=language.value
            )
            reflection_messages = [{"role": "user", "content": reflection_prompt}]
            reflection_response = self.llm_client.chat(reflection_messages) or ""
            if "无需改进" in reflection_response:
                print("代码在算法层面已经达到最优，程序结束")
                break
            self.memory.add_record("reflection", reflection_response)
            refine_prompt = REFINE_PROMPT_TEMPLATE.format(
                task=task,
                last_code_attempt=last_execution,
                feedback=reflection_response,
            )
            refine_messages = [{"role": "user", "content": refine_prompt}]
            refine_response = self.llm_client.chat(refine_messages) or ""
            self.memory.add_record("execution", refine_response)
        return self.memory.get_memory_tracks_str()


if __name__ == "__main__":
    llm_client = HelloAgentsLLM(
        model=os.getenv("LLM_MODEL_ID"),
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY"),
    )
    reflection_agent = ReflectionAgent(llm_client, 10)
    task = input("请输入任务: ")
    language = input(
        "请输入语言(python, java, javascript, typescript, ruby, php, c, cpp, csharp): "
    )
    result = reflection_agent.run(task, Language(language))
    print(result)
