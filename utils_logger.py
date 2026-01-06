#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具模块
提供Logger类用于将输出同时写入终端和文件
"""

import sys


class Logger:
    """将输出同时写入到终端和文件，兼容tqdm进度条"""
    
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', encoding='utf-8')
        # tqdm使用ANSI转义序列，需要特殊处理
        self.is_tqdm_line = False
    
    def write(self, message):
        # 检查是否是tqdm的输出（包含ANSI转义序列）
        if '\r' in message or '\x1b[' in message:
            # tqdm的进度条更新，只写入终端，不写入日志文件
            self.terminal.write(message)
            self.terminal.flush()
        else:
            # 普通输出，同时写入终端和文件
            self.terminal.write(message)
            self.log.write(message)
            self.log.flush()  # 确保实时写入
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        try:
            if self.log and not self.log.closed:
                self.log.close()
        except Exception:
            pass  # 忽略关闭时的异常

