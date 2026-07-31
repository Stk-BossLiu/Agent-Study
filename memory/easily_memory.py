from typing import Any, Dict, List, Optional


class EasilyMemory:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    """
    添加记录
    record_type: 记录类型: reflection, execution
    record_content: 记录内容
    """

    def add_record(self, record_type: str, record_content: str):
        record = {
            "type": record_type,
            "content": record_content,
        }
        print(f"增加一条记忆: {record_type} -> {record_content}")
        self.records.append(record)

    """
    获取记忆轨迹字符串
    返回格式：
    ---上一轮尝试(代码)---\n{record_content}
    ----评审员反馈----\n{record_content}
    """

    def get_memory_tracks_str(self) -> str:
        memory_tracks = []
        for record in self.records:
            record_type = record["type"]
            record_content = record["content"]
            if record_type == "execution":
                memory_tracks.append(f"---上一轮尝试(代码)---\n{record_content}")
            elif record_type == "reflection":
                memory_tracks.append(f"----评审员反馈----\n{record_content}")
        return "\n\n".join(memory_tracks)

    """
    获取最后一轮执行结果
    """

    def get_last_execution(self) -> Optional[str]:
        for record in reversed(self.records):
            if record["type"] == "execution":
                return record["content"]
        return None
