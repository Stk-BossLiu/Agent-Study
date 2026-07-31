from typing import Any, Dict


class ToolExcutor:
    """
    工具执行器，负责执行和管理工具
    """

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, tool_name: str, decription: str, callback: callable):
        if tool_name in self.tools:
            print(f"工具 {tool_name} 已存在, 将覆盖注册")
        self.tools[tool_name] = {
            "description": decription,
            "callback": callback,
        }
        print(f"工具 {tool_name} 注册成功")

    def getTool(self, tool_name: str) -> callable:
        if tool_name not in self.tools:
            print(f"工具 {tool_name} 不存在")
            return None
        return self.tools[tool_name]["callback"]

    def getAvailableTools(self) -> str:
        return "\n".join(
            [f"{name}: {tool['description']}" for name, tool in self.tools.items()]
        )
