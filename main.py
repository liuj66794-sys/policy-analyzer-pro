from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List

# 引入我们刚才编写的模块
from crawler.spiders import OfficialPolicySpider
from crawler.cleaners import PolicyTextCleaner
from nlp_engine.dispatcher import ParallelAnalyzer

app = FastAPI(
    title="中国政策报告智能分析引擎",
    description="聚焦两会、经济工作会议等官方报告的深度 NLP 分析系统",
    version="1.0.0"
)

# 依赖注入组件实例化
spider = OfficialPolicySpider()
# 初始化多进程 NLP 分析器 (限制最大核心数，留出余量给 FastAPI 处理网络请求)
analyzer = ParallelAnalyzer(max_workers=2)


# Pydantic 数据模型
class FetchRequest(BaseModel):
    url: str


class AnalyzeRequest(BaseModel):
    current_text: str
    history_texts: List[str] = []  # 传入历史参考文本用于对比


class BaseResponse(BaseModel):
    status: str
    message: str
    data: dict = {}


@app.post("/api/v1/policy/fetch", response_model=BaseResponse)
async def fetch_and_preprocess_policy(request: FetchRequest):
    """合规抓取官方公开政策报告并进行预处理"""
    try:
        # 1. 异步抓取
        raw_html = await spider.fetch_policy_report(request.url)

        # 2. 文本清洗
        cleaned_text = PolicyTextCleaner.clean_html_noise(raw_html)

        # 3. 生成器分段提取 (演示: 提取前3段预览)
        paragraph_generator = PolicyTextCleaner.chunk_by_paragraph(cleaned_text)
        preview_paragraphs = [next(paragraph_generator) for _ in range(3) if paragraph_generator]

        return BaseResponse(
            status="success",
            message="政策文件抓取与预处理完成",
            data={"preview": preview_paragraphs, "total_length": len(cleaned_text)}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/policy/upload", response_model=BaseResponse)
async def upload_policy_document(file: UploadFile = File(...)):
    """支持用户手动上传非结构化文档 (TXT/PDF/Word)"""
    if not file.filename.endswith(('.txt', '.pdf', '.docx')):
        raise HTTPException(status_code=400, detail="仅支持 TXT, PDF, Word 格式")

    # 读取文本 (此处以 TXT 为例)
    content = await file.read()
    decoded_text = content.decode('utf-8', errors='ignore')
    cleaned_text = PolicyTextCleaner.clean_html_noise(decoded_text)

    return BaseResponse(
        status="success",
        message="文件上传与解析成功",
        data={"filename": file.filename, "text_length": len(cleaned_text)}
    )


@app.post("/api/v1/policy/analyze")
async def analyze_policy_core_logic(request: AnalyzeRequest):
    """
    【真实 AI 接口】：调度五大核心分析逻辑，拉起 CPython 多进程执行张量计算。
    """
    try:
        # 调用多进程调度器，绕过 GIL 执行真实的 NLP 核心算法
        result = await analyzer.run_analysis_async(
            report_text=request.current_text,
            history_texts=request.history_texts
        )

        return {
            "status": "success",
            "message": "深度分析完成",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 分析引擎计算异常: {str(e)}")