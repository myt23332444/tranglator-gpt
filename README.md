# AI 翻译工具

![版本](https://img.shields.io/badge/版本-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.7+-green.svg)
![平台](https://img.shields.io/badge/平台-Windows%20.svg)

一款桌面翻译工具，支持截图和选中，使用大语言模型进行翻译。

<div align="center">
  <img src="docs/screenshot.png" alt="AI翻译工具截图" width="600"/>
</div>

## ✨ 主要特性

- **截图翻译**：框选屏幕区域，自动识别文字并翻译
- **选中翻译**：自动获取剪贴板内容并进行翻译
- **多语种支持**：支持中、英、日、韩等多国语言互译
- **大模型支持**：接入OpenAI等大语言模型进行高质量翻译
- **本地部署**：可连接本地部署的大语言模型，保护隐私
- **全局热键**：无需打开主界面，随时随地一键翻译
- **系统托盘**：最小化至系统托盘，不占用桌面空间

## 📥 安装说明

### 前置条件

- Python 3.7 或更高版本
- Tesseract OCR (用于文字识别)

### 1. 克隆仓库

```bash
git clone ...
cd ...
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装 Tesseract OCR

#### Windows
1. 从[Github官方页面](https://github.com/UB-Mannheim/tesseract/wiki)下载安装包
2. 安装时记录下安装路径
3. 在程序设置中设置 Tesseract 路径


### 4. 设置API密钥

将 `.env.example` 复制为 `.env` 并添加你的 API 密钥：

```
OPENAI_API_KEY=你的OpenAI密钥
```

## 🚀 快速开始

### 启动应用

```bash
python run.py
```

首次运行时，程序会自动检查依赖并进行必要的配置。

### 使用方法

- **截图翻译**: 按下 `Ctrl+Alt+S` (可自定义)，框选屏幕区域
- **选中翻译**: 选中任意文本，按下 `Ctrl+Alt+T` (可自定义)
- **手动输入**: 在主界面输入文本，点击"翻译"按钮

## ⚙️ 高级配置

### 设置界面

点击系统托盘图标，选择"设置"进入设置界面：

1. **API设置**: 选择翻译服务（OpenAI/本地模型），配置API参数
2. **OCR设置**: 设置Tesseract路径，配置OCR语言
3. **热键设置**: 自定义全局热键组合

### 本地模型配置

要使用本地部署的大语言模型：

1. 在设置中选择翻译服务为"local_llm"
2. 填入本地模型的API端点，如 `http://localhost:8000/v1/chat/completions`
3. 设置模型名称和参数

## 🛠️ 技术架构

- **UI框架**: PyQt5
- **OCR引擎**: Tesseract
- **图像处理**: PIL (Pillow)
- **翻译后端**: OpenAI API / 自定义LLM API
- **全局热键**: keyboard

## 📄 项目结构（目前功能并不完善）

```
ai-translator/
├── translator.py      # 主程序
├── llm_service.py     # 翻译服务模块
├── run.py             # 启动脚本
├── requirements.txt   # 依赖列表
├── config.json        # 配置文件
├── .env               # 环境变量（API密钥）
└── docs/              # 文档图片等资源
```

## 🔧 常见问题

### OCR识别不准确

- 确保已安装最新版本的Tesseract
- 在设置中添加需要识别的语言
- 截图时保持图像清晰，避免背景复杂

### 无法连接到API

- 检查网络连接
- 确认API密钥正确
- 确认API端点可访问

### 热键无效

- 检查是否与其他应用热键冲突
- 尝试在设置中修改热键组合
- 重启应用后再试

## 🔜 未来计划

- [ ] 支持更多翻译API
- [ ] 增加历史记录功能
- [ ] 添加语音输入/输出
- [ ] 提供更多自定义主题
- [ ] 优化OCR识别准确率



## 🙏 致谢

- [OpenAI](https://openai.com/) - 提供高质量翻译API
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR引擎
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI框架
