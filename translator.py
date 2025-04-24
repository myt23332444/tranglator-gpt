#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
翻译工具 - 支持截图翻译和选中翻译
"""

import sys
import os
import io
import time
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon, QMenu, 
                             QAction, QLabel, QVBoxLayout, QHBoxLayout, QWidget, 
                             QPushButton, QTextEdit, QComboBox, QMessageBox,
                             QDialog, QLineEdit, QFormLayout, QTabWidget, QCheckBox)
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QThread, QSize
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QPen, QColor, QCursor
import pytesseract
from PIL import Image, ImageGrab
import pyperclip
import keyboard
import requests
from dotenv import load_dotenv

# 导入翻译服务模块
from llm_service import translate_text

# 加载环境变量
load_dotenv()


class SnippingWidget(QWidget):
    """截图工具"""
    closed = pyqtSignal(QPixmap)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowState(Qt.WindowFullScreen)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 100);")
        self.begin = QPoint()
        self.end = QPoint()
        self.show()

    def paintEvent(self, event):
        """绘制截图区域"""
        if not self.begin.isNull() and not self.end.isNull():
            qp = QPainter(self)
            qp.setPen(QPen(QColor(255, 0, 0), 2))
            rect = QRect(self.begin, self.end)
            qp.drawRect(rect)
            # 绘制半透明遮罩
            qp.fillRect(self.rect(), QColor(0, 0, 0, 100))
            # 清除选中区域的遮罩
            qp.fillRect(rect, QColor(0, 0, 0, 0))

    def mousePressEvent(self, event):
        """鼠标按下"""
        self.begin = event.pos()
        self.end = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        """鼠标移动"""
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        self.end = event.pos()
        self.capture_screenshot()

    def capture_screenshot(self):
        """捕获截图"""
        if self.begin == self.end:
            self.close()
            return
        
        x1, y1 = min(self.begin.x(), self.end.x()), min(self.begin.y(), self.end.y())
        x2, y2 = max(self.begin.x(), self.end.x()), max(self.begin.y(), self.end.y())
        
        # 全屏截图
        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        
        # 转换为QPixmap
        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG')
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())

        self.closed.emit(pixmap)
        self.close()


class TranslationThread(QThread):
    """翻译线程"""
    translation_done = pyqtSignal(str)
    
    def __init__(self, text, target_lang):
        super().__init__()
        self.text = text
        self.target_lang = target_lang
        
    def run(self):
        """运行翻译"""
        translated_text = translate_text(self.text, self.target_lang)
        self.translation_done.emit(translated_text)


class SettingsDialog(QDialog):
    """设置对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        
        # 加载配置
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {
                "translation_service": "openai",
                "services": {
                    "openai": {
                        "model": "gpt-3.5-turbo",
                        "temperature": 0.3,
                        "api_endpoint": "https://api.openai.com/v1/chat/completions"
                    },
                    "local_llm": {
                        "model": "model_name",
                        "temperature": 0.3,
                        "api_endpoint": "http://localhost:8000/v1/chat/completions"
                    }
                },
                "ocr": {
                    "tesseract_path": "",
                    "languages": ["eng", "chi_sim", "jpn", "kor"]
                },
                "hotkeys": {
                    "screenshot": "ctrl+alt+s",
                    "selection": "ctrl+alt+t"
                }
            }
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # API设置选项卡
        api_tab = QWidget()
        api_layout = QFormLayout()
        
        # 翻译服务选择
        self.service_combo = QComboBox()
        self.service_combo.addItems(["openai", "local_llm"])
        self.service_combo.setCurrentText(self.config["translation_service"])
        self.service_combo.currentTextChanged.connect(self.update_service_form)
        api_layout.addRow("翻译服务:", self.service_combo)
        
        # OpenAI设置
        self.openai_model = QLineEdit(self.config["services"]["openai"]["model"])
        self.openai_temp = QLineEdit(str(self.config["services"]["openai"]["temperature"]))
        self.openai_endpoint = QLineEdit(self.config["services"]["openai"]["api_endpoint"])
        api_layout.addRow("OpenAI模型:", self.openai_model)
        api_layout.addRow("Temperature:", self.openai_temp)
        api_layout.addRow("API端点:", self.openai_endpoint)
        
        # 本地LLM设置
        self.local_model = QLineEdit(self.config["services"]["local_llm"]["model"])
        self.local_temp = QLineEdit(str(self.config["services"]["local_llm"]["temperature"]))
        self.local_endpoint = QLineEdit(self.config["services"]["local_llm"]["api_endpoint"])
        api_layout.addRow("本地模型:", self.local_model)
        api_layout.addRow("Temperature:", self.local_temp)
        api_layout.addRow("API端点:", self.local_endpoint)
        
        api_tab.setLayout(api_layout)
        
        # OCR设置选项卡
        ocr_tab = QWidget()
        ocr_layout = QFormLayout()
        
        self.tesseract_path = QLineEdit(self.config["ocr"]["tesseract_path"])
        ocr_layout.addRow("Tesseract路径:", self.tesseract_path)
        
        # 语言复选框
        lang_layout = QVBoxLayout()
        self.lang_checkboxes = {}
        all_langs = ["eng", "chi_sim", "chi_tra", "jpn", "kor", "fra", "deu", "spa", "rus"]
        for lang in all_langs:
            cb = QCheckBox(lang)
            cb.setChecked(lang in self.config["ocr"]["languages"])
            self.lang_checkboxes[lang] = cb
            lang_layout.addWidget(cb)
        
        ocr_layout.addRow("OCR语言:", QWidget())
        ocr_tab.setLayout(ocr_layout)
        
        # 热键设置选项卡
        hotkey_tab = QWidget()
        hotkey_layout = QFormLayout()
        
        self.screenshot_hotkey = QLineEdit(self.config["hotkeys"]["screenshot"])
        self.selection_hotkey = QLineEdit(self.config["hotkeys"]["selection"])
        
        hotkey_layout.addRow("截图翻译热键:", self.screenshot_hotkey)
        hotkey_layout.addRow("选中翻译热键:", self.selection_hotkey)
        
        hotkey_tab.setLayout(hotkey_layout)
        
        # 添加选项卡
        tab_widget.addTab(api_tab, "API设置")
        tab_widget.addTab(ocr_tab, "OCR设置")
        tab_widget.addTab(hotkey_tab, "热键设置")
        
        # 按钮
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(tab_widget)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def update_service_form(self):
        """根据选择的服务更新表单"""
        service = self.service_combo.currentText()
        if service == "openai":
            self.openai_model.setEnabled(True)
            self.openai_temp.setEnabled(True)
            self.openai_endpoint.setEnabled(True)
            self.local_model.setEnabled(False)
            self.local_temp.setEnabled(False)
            self.local_endpoint.setEnabled(False)
        else:
            self.openai_model.setEnabled(False)
            self.openai_temp.setEnabled(False)
            self.openai_endpoint.setEnabled(False)
            self.local_model.setEnabled(True)
            self.local_temp.setEnabled(True)
            self.local_endpoint.setEnabled(True)
    
    def save_settings(self):
        """保存设置"""
        try:
            # 更新配置
            self.config["translation_service"] = self.service_combo.currentText()
            
            # OpenAI设置
            self.config["services"]["openai"]["model"] = self.openai_model.text()
            self.config["services"]["openai"]["temperature"] = float(self.openai_temp.text())
            self.config["services"]["openai"]["api_endpoint"] = self.openai_endpoint.text()
            
            # 本地LLM设置
            self.config["services"]["local_llm"]["model"] = self.local_model.text()
            self.config["services"]["local_llm"]["temperature"] = float(self.local_temp.text())
            self.config["services"]["local_llm"]["api_endpoint"] = self.local_endpoint.text()
            
            # OCR设置
            self.config["ocr"]["tesseract_path"] = self.tesseract_path.text()
            
            # 语言设置
            selected_langs = []
            for lang, cb in self.lang_checkboxes.items():
                if cb.isChecked():
                    selected_langs.append(lang)
            self.config["ocr"]["languages"] = selected_langs
            
            # 热键设置
            self.config["hotkeys"]["screenshot"] = self.screenshot_hotkey.text()
            self.config["hotkeys"]["selection"] = self.selection_hotkey.text()
            
            # 保存到文件
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            
            # 设置Tesseract路径
            if self.tesseract_path.text():
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_path.text()
            
            QMessageBox.information(self, "成功", "设置已保存")
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存设置失败: {str(e)}")


class TranslatorApp(QMainWindow):
    """翻译应用主窗口"""
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("AI翻译工具")
        self.setGeometry(100, 100, 600, 400)
        
        # 加载配置
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                self.config = json.load(f)
                
            # 设置Tesseract路径
            if self.config["ocr"].get("tesseract_path"):
                pytesseract.pytesseract.tesseract_cmd = self.config["ocr"]["tesseract_path"]
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {
                "translation_service": "openai",
                "services": {
                    "openai": {
                        "model": "gpt-3.5-turbo",
                        "temperature": 0.3
                    }
                },
                "hotkeys": {
                    "screenshot": "ctrl+alt+s",
                    "selection": "ctrl+alt+t"
                }
            }
        
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("AI翻译工具")
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        screenshot_action = QAction("截图翻译", self)
        screenshot_action.triggered.connect(self.start_screenshot)
        
        selection_action = QAction("选中翻译", self)
        selection_action.triggered.connect(self.translate_selection)
        
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        
        tray_menu.addAction(screenshot_action)
        tray_menu.addAction(selection_action)
        tray_menu.addAction(settings_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # 默认使用一个简单的图标
        self.tray_icon.setIcon(QIcon.fromTheme("accessories-dictionary"))
        self.tray_icon.show()
        
        # 创建主界面
        self.init_ui()
        
        # 注册全局热键
        self.register_hotkeys()
        
    def init_ui(self):
        """初始化UI界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # 源文本和翻译结果
        self.source_text = QTextEdit()
        self.source_text.setPlaceholderText("输入要翻译的文本...")
        
        self.target_text = QTextEdit()
        self.target_text.setPlaceholderText("翻译结果将显示在这里...")
        self.target_text.setReadOnly(True)
        
        # 语言选择
        lang_layout = QHBoxLayout()
        target_lang_label = QLabel("目标语言:")
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems(["中文", "英文", "日文", "韩文", "法文", "德文", "西班牙文"])
        
        lang_layout.addWidget(target_lang_label)
        lang_layout.addWidget(self.target_lang_combo)
        lang_layout.addStretch(1)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 翻译按钮
        translate_btn = QPushButton("翻译")
        translate_btn.clicked.connect(self.translate_input)
        
        # 截图翻译按钮
        screenshot_btn = QPushButton("截图翻译")
        screenshot_btn.clicked.connect(self.start_screenshot)
        
        button_layout.addWidget(translate_btn)
        button_layout.addWidget(screenshot_btn)
        button_layout.addStretch(1)
        
        # 布局
        layout.addWidget(QLabel("原文:"))
        layout.addWidget(self.source_text)
        layout.addLayout(lang_layout)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("翻译:"))
        layout.addWidget(self.target_text)
        
        central_widget.setLayout(layout)
    
    def register_hotkeys(self):
        """注册全局热键"""
        # 先解绑所有热键
        keyboard.unhook_all()
        
        # 获取当前配置的热键
        screenshot_key = self.config["hotkeys"].get("screenshot", "ctrl+alt+s")
        selection_key = self.config["hotkeys"].get("selection", "ctrl+alt+t")
        
        # 注册热键
        keyboard.add_hotkey(screenshot_key, self.start_screenshot)
        keyboard.add_hotkey(selection_key, self.translate_selection)
    
    def start_screenshot(self):
        """开始截图流程"""
        self.hide()  # 隐藏主窗口
        
        # 等待一小段时间以确保窗口隐藏
        time.sleep(0.2)
        
        # 创建截图窗口
        self.snipper = SnippingWidget()
        self.snipper.closed.connect(self.process_screenshot)
    
    def process_screenshot(self, pixmap):
        """处理截图并进行OCR"""
        if pixmap.isNull():
            self.show()
            return
        
        # 将QPixmap转换为PIL.Image进行OCR
        image = ImageGrab.grabclipboard()
        if image is None:
            # 如果剪贴板没有图片，从QPixmap转换
            buffer = QPixmap(pixmap).toImage()
            buffer.save("temp_screenshot.png")
            image = Image.open("temp_screenshot.png")
            os.remove("temp_screenshot.png")
        
        # OCR识别
        try:
            # 获取配置的语言
            lang_config = "+".join(self.config["ocr"].get("languages", ["eng"]))
            if not lang_config:
                lang_config = "eng"
            
            text = pytesseract.image_to_string(image, lang=lang_config)
            
            # 显示窗口并填充识别的文本
            self.show()
            self.source_text.setText(text.strip())
            
            # 自动翻译
            self.translate_input()
        except Exception as e:
            QMessageBox.warning(self, "OCR错误", f"图像文本识别失败: {str(e)}")
            self.show()
    
    def translate_selection(self):
        """翻译选中的文本"""
        # 获取系统剪贴板中的文本
        selected_text = pyperclip.paste()
        
        if not selected_text:
            QMessageBox.information(self, "提示", "没有检测到选中的文本")
            return
        
        # 显示窗口并填充选中的文本
        self.show()
        self.source_text.setText(selected_text)
        
        # 翻译文本
        self.translate_input()
    
    def translate_input(self):
        """翻译输入框中的文本"""
        text = self.source_text.toPlainText()
        
        if not text:
            QMessageBox.information(self, "提示", "请输入需要翻译的文本")
            return
        
        target_lang = self.target_lang_combo.currentText()
        
        # 创建并启动翻译线程
        self.translation_thread = TranslationThread(text, target_lang)
        self.translation_thread.translation_done.connect(self.update_translation)
        self.translation_thread.start()
        
        # 禁用翻译按钮，显示翻译中
        self.target_text.setText("翻译中...")
    
    def update_translation(self, translated_text):
        """更新翻译结果"""
        self.target_text.setText(translated_text)
    
    def show_settings(self):
        """显示设置界面"""
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec_() == QDialog.Accepted:
            # 重新加载配置
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                
                # 重新注册热键
                self.register_hotkeys()
                
                # 设置Tesseract路径
                if self.config["ocr"].get("tesseract_path"):
                    pytesseract.pytesseract.tesseract_cmd = self.config["ocr"]["tesseract_path"]
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载配置失败: {str(e)}")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 如果是从托盘菜单关闭的，退出应用
        if getattr(self, '_exiting', False):
            event.accept()
            return
        
        # 最小化到托盘而不是关闭
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
    
    def quit_application(self):
        """完全退出应用"""
        self._exiting = True
        keyboard.unhook_all()  # 解绑所有热键
        self.close()
        QApplication.quit()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出应用
    
    translator = TranslatorApp()
    translator.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()