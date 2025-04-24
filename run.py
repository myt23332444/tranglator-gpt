#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI翻译工具启动脚本
"""

import os
import sys
import subprocess
import traceback

def check_dependencies():
    """检查依赖并安装缺失的包"""
    try:
        import PyQt5
        import pytesseract
        import PIL
        import pyperclip
        import keyboard
        import requests
        import openai
        import dotenv
        
        print("所有依赖已安装，正在启动程序...")
        return True
    except ImportError as e:
        missing_pkg = str(e).split("'")[1]
        print(f"缺少依赖: {missing_pkg}")
        
        try:
            print(f"正在安装 {missing_pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("依赖安装完成")
            return check_dependencies()  # 递归检查是否所有依赖都已安装
        except Exception as e:
            print(f"安装依赖失败: {str(e)}")
            return False

def check_tesseract():
    """检查Tesseract OCR是否已安装"""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("Tesseract OCR 已安装")
        return True
    except Exception:
        if sys.platform.startswith('win'):
            print("未检测到Tesseract OCR。请从以下地址安装：")
            print("https://github.com/UB-Mannheim/tesseract/wiki")
        elif sys.platform.startswith('darwin'):  # macOS
            print("未检测到Tesseract OCR。请使用以下命令安装：")
            print("brew install tesseract")
        else:  # Linux
            print("未检测到Tesseract OCR。请使用以下命令安装：")
            print("sudo apt install tesseract-ocr")
        return False

def main():
    """主函数"""
    print("正在启动AI翻译工具...")
    
    # 检查依赖
    if not check_dependencies():
        input("按Enter键退出...")
        return
    
    # 检查Tesseract
    check_tesseract()
    
    # 检查配置文件
    if not os.path.exists("config.json"):
        print("未找到配置文件，将使用默认配置")
    
    # 检查环境变量
    if not os.path.exists(".env"):
        print("未找到.env文件，将创建示例文件")
        with open(".env", "w", encoding="utf-8") as f:
            f.write("# 填入你的API密钥\n")
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
        print("请在.env文件中填入你的API密钥")
    
    try:
        # 启动翻译应用
        from translator import main as translator_main
        translator_main()
    except Exception as e:
        print(f"启动失败: {str(e)}")
        traceback.print_exc()
        input("按Enter键退出...")

if __name__ == "__main__":
    main()