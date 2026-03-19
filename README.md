# 🏛️ 中国政策报告智能分析引擎 (Policy-Analyzer-Pro)

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25+-red.svg)](https://streamlit.io/)
[![NLP](https://img.shields.io/badge/Model-Chinese--RoBERTa-orange.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 简介

本项目是一个基于 **CPython 多进程架构**与 **Transformer 深度语义向量** 构建的智能分析引擎。它专为解读两会、经济工作会议等官方政策报告设计，能够跨文档精准测算历届报告的措辞变化、核心导向演变、新提法以及议题的动态删减。

**🏆 Pro 版核心进化**：全面实现 **100% 离线张量计算**与**状态持久化 (Session State)**，拒绝网络波动，支持生成专业级 Markdown 变迁简报。

![系统大屏主界面截图](./app_screenshot.png)

## ✨ 核心亮点功能

* **📴 纯离线推理锁**: 底层强制注入 `HF_HUB_OFFLINE`，模型随取随用，彻底根除 HuggingFace 403 网络阻断报错。
* **⚖️ 历届政策双篇比对**:
    * **语义演变**: 基于 Cosine Similarity 精准测算旧话新说的“变化强度”。
    * **动态删减监测**: 独创基于 TextRank 的核心议题提取与新稿词频密度衰减比对，智能判定【彻底删减】与【明显弱化】。
* **📄 全格式文档解析**: 集成 `pdfplumber` 与 `python-docx`，支持 PDF/DOCX/TXT 本地拖拽解析，及严格遵循 `robots.txt` 的异步网页合规抓取。
* **🚀 多进程并行调度**: 绕过 Python GIL 锁，子进程独立初始化 Transformer 模型（防 OOM 与 IPC 序列化开销），极致榨干 CPU。
* **📥 商用级简报导出**: 一键将对比分析成果导出为排版精美的 Markdown 报告，完美兼容 Typora 转 PDF。

## 🛠️ 技术栈

| 模块 | 核心技术 | 工程作用 |
| :--- | :--- | :--- |
| **Frontend** | Streamlit | 响应式交互大屏，基于 `session_state` 的数据防丢缓存 |
| **Backend** | FastAPI | 异步高性能 RESTful API，处理网络 I/O 与并发请求 |
| **NLP Core** | SentenceTransformers | `chinese-roberta-wwm-ext` 语义高维特征提取 |
| **Algorithm** | Jieba (TextRank), Numpy | 文本清洗、图排序提取核心议题、余弦相似度计算 |
| **Dispatcher** | ProcessPoolExecutor | CPython 多进程调度池，隔离大模型内存，解决阻塞 |

## 📥 部署与准备

1.  **环境安装**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **字体支持 (必须)**:
    系统词云生成依赖中文字体。请自行下载 `simhei.ttf` (黑体) 并放入项目根目录。
3.  **模型准备**:
    首次运行会自动下载约 400MB 语言模型至本地缓存。后续启动受离线锁保护，实现秒开。

## 🚀 快速启动

1.  **启动后端计算中枢 (终端 1)**:
    ```bash
    uvicorn main:app --port 8000
    ```
2.  **启动前端可视化大屏 (终端 2)**:
    ```bash
    streamlit run frontend/app.py
    ```

## 📃 开源协议
本项目基于 [MIT License](LICENSE) 协议开源。
