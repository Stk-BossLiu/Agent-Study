import asyncio
import json
import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

from pydantic import BaseModel, Field
from tavily import TavilyClient


load_dotenv()


class SearchState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str
    search_query: str
    search_results: str
    final_answer: str
    step: str


class UnderstandQueryOutput(BaseModel):
    understanding: str = Field(description="用户需求理解")
    search_keywords: str = Field(description="最佳搜索关键词")


class SearchAssistant:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL_ID"),
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            temperature=0.7,
        )
        self.tavilyClient = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    def create_search_assitant(self):
        workflow = StateGraph(SearchState)
        workflow.add_node("understand_query", self.understand_query_node)
        workflow.add_node("search", self.search_node)
        workflow.add_node("answer", self.answer_node)
        workflow.add_edge(START, "understand_query")
        workflow.add_edge("understand_query", "search")
        workflow.add_edge("search", "answer")
        workflow.add_edge("answer", END)

        memory = InMemorySaver()
        app = workflow.compile(checkpointer=memory)
        return app

    # 理解用户需求
    def understand_query_node(self, state: SearchState):
        user_message = state["messages"][-1].content  # 查询最新的一条消息
        understand_prompt = f"""分析用户的查询："{user_message}"
请完成两个任务：
1. 简洁总结用户想要了解什么
2. 生成最适合搜索引擎的关键词（中英文均可，要精准）

"""
        parser = JsonOutputParser(pydantic_object=UnderstandQueryOutput)
        prompt = understand_prompt + "\n" + parser.get_format_instructions()
        response = self.llm.invoke([SystemMessage(content=prompt)])
        data = json.loads(response.content)
        return {
            "user_query": response.content,
            "search_query": data.get("search_keywords", ""),
            "step": "understood",
            "messages": [
                AIMessage(
                    content="这是我对你需求的理解：" + data.get("understanding", "")
                )
            ],
        }

    def search_node(self, state: SearchState):
        search_query = state["search_query"]
        search_results = ""
        try:
            print("=" * 20 + "searching..." + "=" * 20)
            response = self.tavilyClient.search(
                query=search_query,
                search_depth="basic",
                include_answer=True,
                include_raw_content=True,
                max_results=5,
            )
            # 处理搜索结果
            if response.get("answer"):
                search_results = f"综合答案: {response['answer']}\n\n"

            if response.get("results"):
                search_results += "相关信息: \n"
                for i, result in enumerate(response["results"][:3]):
                    title = result.get("title", "无标题")
                    url = result.get("url", "无URL")
                    content = result.get("content", "无内容")
                    search_results += f"第{i+1}条: {title}\n{content}\n来源: {url}\n\n"
            return {
                "search_results": search_results,
                "step": "searched",
                "messages": [
                    AIMessage(
                        content="✅ 搜索完成！找到了相关信息，正在为您整理答案..."
                    )
                ],
            }
        except Exception as e:
            print(f"Error: {e}")
            return {
                "search_results": f"搜索结果获取失败: {e}",
                "step": "search_failed",
                "messages": [
                    AIMessage(content="搜索结果获取失败: 我将基于已有知识为您回答")
                ],
            }

    def answer_node(self, state: SearchState):
        search_results = state["search_results"]
        if state["step"] == "search_failed":
            fallback_prompt = f"""搜索API暂时不可用，请基于您的知识回答用户的问题：

用户问题：{state['user_query']}

请提供一个有用的回答，并说明这是基于已有知识的回答。"""
            response = self.llm.invoke([SystemMessage(content=fallback_prompt)])
            return {
                "final_answer": response.content,
                "step": "answered",
                "messages": [AIMessage(content=response.content)],
            }
        else:
            answer_prompt = f"""
            你是一个专业的信息整理专家，现在用户的问题是："{state["user_query"]}"
            请要求：
              1. 综合搜索结果，提供准确、有用的回答
              2. 如果是技术问题，提供具体的解决方案或代码
              3. 引用重要信息的来源
              4. 回答要结构清晰、易于理解
              5. 如果搜索结果不够完整，请说明并提供补充建议
            我已经搜索到了相关信息，请根据这些信息整理出一份简洁明了的答案，答案要简洁明了，不要超过500字。
            相关信息:
            {search_results}
            """
            response = self.llm.invoke([SystemMessage(content=answer_prompt)])
            return {
                "final_answer": response.content,
                "step": "answered",
                "messages": [AIMessage(content=response.content)],
            }


async def main():
    workflow = SearchAssistant()
    app = workflow.create_search_assitant()
    session_count = 0
    while True:
        user_input = input("请输入你的查询: ")

        if user_input.lower() == "exit":
            print("退出程序")
            break
        if not user_input:
            continue
        session_count += 1
        config = {"configurable": {"thread_id": f"search_session_{session_count}"}}
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_query": "",
            "search_query": "",
            "search_results": "",
            "final_answer": "",
            "step": "understand_query",
        }
        try:
            print("\n" + "=" * 60)
            async for output in app.astream(initial_state, config=config):
                for node_name, node_output in output.items():
                    print(node_name, node_output)
                    if "messages" in node_output and node_output["messages"]:
                        latest_message = node_output["messages"][-1]

                        if isinstance(latest_message, AIMessage):
                            if node_name == "understand_query":
                                print(f"🧠 理解阶段: {latest_message.content}")
                            elif node_name == "search":
                                print(f"🔍 搜索阶段: {latest_message.content}")
                            elif node_name == "answer":
                                print(f"💬 回答阶段: {latest_message.content}")
            print("\n" + "=" * 60 + "\n")
        except Exception as e:
            print(f"Error: {e}")
            continue


if __name__ == "__main__":
    asyncio.run(main())
