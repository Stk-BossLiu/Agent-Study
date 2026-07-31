"""
数学计算工具
"""

description = "一个数学计算工具。当你需要进行数学计算时，应使用此工具。"

from sympy import sympify


def caculate(expression: str) -> str:
    try:
        result = sympify(expression)
        return str(result)
    except Exception as e:
        return str(e)
