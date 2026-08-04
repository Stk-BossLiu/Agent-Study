from typing import List
from agentscope.agent import Agent


GAME_ROLES_NAME = [
    "刘备",
    "关羽",
    "张飞",
    "诸葛亮",
    "赵云",
    "曹操",
    "司马懿",
    "典韦",
    "许褚",
    "夏侯惇",
    "孙权",
    "周瑜",
    "陆逊",
    "甘宁",
    "太史慈",
    "吕布",
    "貂蝉",
    "董卓",
    "袁绍",
    "袁术",
]
MAX_GAME_ROUND = 10
MAX_DISCUSSION_ROUND = 3


def format_player_list(players: List[Agent], show_roles: bool = False) -> str:
    """格式化玩家列表为中文显示"""
    if not players:
        return "无玩家"

    if show_roles:
        return "、".join([f"{p.name}({getattr(p, 'role', '未知')})" for p in players])
    else:
        return "、".join([p.name for p in players])


def format_player_list_str(players: List[str]) -> str:
    """格式化玩家姓名列表"""
    if not players:
        return "无人"
    return "、".join(players)
