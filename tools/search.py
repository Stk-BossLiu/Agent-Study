from ast import Dict, List
from typing import Any
from serpapi import Client
from dotenv import load_dotenv
import os

load_dotenv()

description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"


def search(query: str) -> str:
    print(f"正在搜索：{query}")
    try:
        api_key = os.getenv("SERPAPI_KEY")
        print(f"api_key: {api_key}")
        client = Client(api_key=api_key)
        results = client.search(
            {
                "engine": "google",
                "q": query,
                "location": "Wuhan, China",
                "gl": "cn",
                "hl": "zh-CN",
            }
        ).as_dict()
        answer_box = results.get("answer_box", None)
        if answer_box:
            return f"{answer_box.get('title', '')}\n{answer_box.get('snippet_highlighted_words','')}\n{answer_box.get('snippet', '')}"
        organic_results: List[Dict[str, Any]] = results.get("organic_results", [])
        if len(organic_results) == 0:
            print("搜索工具有问题。")
            return None
        snippts = []
        # 找前5个搜索结果信息
        for i, result in enumerate(organic_results[:5]):
            snippt = f"{i+1}. {result.get('title', '')}\n{result.get('snippet', '')}"
            snippts.append(snippt)
        return "\n".join(snippts)
    except Exception as e:
        print(f"搜素工具发生错误: {e}")
        return None
