from serpapi import Client
import os

from main import client


def search(query: str) -> str:
    print(f"正在搜索：{query}")
    try:
        api_key = os.getenv("SERPAPI_KEY")
        client = Client(api_key)
        results = client.search(
            {
                "engine": "google",
                "q": query,
                "location": "Wuhan, China",
                "gl": "cn",
                "hl": "zh-CN",
            }
        ).as_dict()
        results.as_dict()
    except Exception as e:
        print(f"搜素工具发生错误: {e}")
        return None
