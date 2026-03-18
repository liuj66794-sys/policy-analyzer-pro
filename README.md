# 🏛️ 中国政策报告智能分析引擎 (Policy-Analyzer-Pro)

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

基于 **CPython 多进程架构**与 **Transformer 语义向量**开发的深度分析工具，专门用于解读两会、经济工作会议等官方报告的措辞变化与核心导向。

## ✨ 核心功能
* **合规异步抓取**：严格遵循 robots 协议，利用 `httpx` 异步爬取官方网页。
* **多进程 NLP 引擎**：绕过 Python GIL 锁，利用 `ProcessPoolExecutor` 执行张量计算。
* **措辞变化测算**：基于语义相似度算法，精确识别历届报告中“微调”的表述。
* **热点可视化**：自动提取新提法并生成高频词云图。

## 🛠️ 技术栈
* **前端**: Streamlit (响应式数据大屏)
* **后端**: FastAPI (异步高性能 RESTful API)
* **模型**: Chinese-RoBERTa-WWM-Ext (中文深度语义理解)
* **底层**: Python 多进程、Pandas、WordCloud

## 🚀 快速启动
1.  **安装依赖**: `pip install -r requirements.txt`
2.  **启动后端**: `uvicorn main:app --port 8000`
3.  **启动前端**: `streamlit run frontend/app.py`
4.  **准备字体**: 确保根目录下有 `simhei.ttf` 字体文件。

## ⚠️ 免责声明
本软件分析结果仅供学术交流与政策研究参考，不构成任何决策建议，解读请以官方发布稿为准。
