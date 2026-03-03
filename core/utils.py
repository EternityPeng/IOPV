"""
工具函数模块
"""

import os
from datetime import datetime
from typing import Optional


def ensure_dir(path: str) -> str:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        str: 目录路径
    """
    os.makedirs(path, exist_ok=True)
    return path


def format_time(dt: datetime = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化时间
    
    Args:
        dt: datetime对象，默认为当前时间
        fmt: 格式字符串
        
    Returns:
        str: 格式化后的时间字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)


def format_number(num: Optional[float], decimals: int = 2, suffix: str = "") -> str:
    """
    格式化数字
    
    Args:
        num: 数字
        decimals: 小数位数
        suffix: 后缀
        
    Returns:
        str: 格式化后的字符串
    """
    if num is None:
        return "--"
    return f"{num:.{decimals}f}{suffix}"


def format_percentage(num: Optional[float], decimals: int = 2) -> str:
    """
    格式化百分比
    
    Args:
        num: 数字
        decimals: 小数位数
        
    Returns:
        str: 格式化后的字符串
    """
    if num is None:
        return "--"
    if num >= 0:
        return f"+{num:.{decimals}f}%"
    return f"{num:.{decimals}f}%"
