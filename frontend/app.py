import streamlit as st
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import requests

# 预设的 FastAPI 后端地址
BACKEND_URL = "http://localhost:8000/api/v1/policy"

# ==========================================
# 法律合规与免责声明 (硬编码强制展示)
# ==========================================
st.set_page_config(page_title="中国政策报告智能分析系统", layout="wide")
st.warning(
    "⚠️ **合规免责声明**：本软件分析结果仅供参考，不构成任何决策建议，"
    "政策解读以官方发布为准，开发者不对因使用本软件导致的任何决策损失承担责任。全流程不存储用户个人隐私数据。"
)

st.title("🏛️ 政策报告智能分析引擎 (Demo 版)")
st.markdown("基于 CPython 多进程架构与 Transformer 语义向量的深度分析工具")

# ==========================================
# 状态缓存：记录当前准备分析的文本 (硬核路线核心组件)
# ==========================================
if "current_report_text" not in st.session_state:
    st.session_state.current_report_text = ""

# ==========================================
# 侧边栏：数据输入模块
# ==========================================
with st.sidebar:
    st.header("1. 报告导入")
    input_mode = st.radio("选择导入方式", ["使用内置 Demo 语料", "输入官方 URL", "手动上传文件"])

    if input_mode == "使用内置 Demo 语料":
        demo_text = """
        深入推进教育强省建设。优化职业教育类型定位，扩大高质量专升本招生规模，畅通技能人才职业发展通道。
        坚持把高质量充分就业作为经济社会发展的优先目标。强化宏观调控，培育新质生产力，加快建设现代化产业体系。
        我们将持续深化科技体制改革，全面提升自主创新能力，扎实推进乡村全面振兴。
        """
        st.text_area("当前分析语料预览", value=demo_text, height=200, disabled=True)
        # 将文本写入内存，等待主界面调用
        st.session_state.current_report_text = demo_text

    elif input_mode == "输入官方 URL":
        url = st.text_input("输入目标网页链接 (例如广东省人民政府网)")
        if st.button("合规抓取"):
            # noinspection PyTypeChecker
            with st.spinner("正在呼叫 FastAPI 后端，严格遵循 robots 协议抓取..."):
                if not url:
                    st.warning("请先输入链接！")
                else:
                    try:
                        response = requests.post(f"{BACKEND_URL}/fetch", json={"url": url})
                        if response.status_code == 200:
                            res_data = response.json()["data"]
                            st.success(f"真实抓取成功！获取文本总长度: {res_data['total_length']} 字")
                            preview_text = "\n\n".join(res_data["preview"])
                            st.text_area("真实抓取结果预览 (前3段)", value=preview_text, height=200)
                            # 将抓取到的文本写入内存
                            st.session_state.current_report_text = preview_text
                        else:
                            st.error(f"后端抓取报错了: {response.json().get('detail', '未知错误')}")
                    except requests.exceptions.ConnectionError:
                        st.error("无法连接到后端！请检查终端是否已经运行了 `uvicorn main:app ...`")

    elif input_mode == "手动上传文件":
        uploaded_file = st.file_uploader("支持 TXT 纯文本文件", type=['txt'])
        if uploaded_file is not None:
            if st.button("开始真实解析"):
                # noinspection PyTypeChecker
                with st.spinner("正在将文件传输至 FastAPI 后端..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                        response = requests.post(f"{BACKEND_URL}/upload", files=files)
                        if response.status_code == 200:
                            res_data = response.json()["data"]
                            st.success(f"真实解析成功！有效文本长度: {res_data['text_length']} 字")
                            # 从前台直接解码文件，写入全局内存
                            file_content = uploaded_file.getvalue().decode('utf-8', errors='ignore')
                            st.session_state.current_report_text = file_content
                        else:
                            st.error(f"解析报错: {response.json().get('detail', '未知错误')}")
                    except requests.exceptions.ConnectionError:
                        st.error("无法连接到后端！请检查 uvicorn 是否运行。")

# ==========================================
# 主界面：真实 AI 分析引擎接入
# ==========================================
if st.button("🚀 启动深度核心分析", type="primary"):

    # 检查内存里有没有真实拿到的文本
    if not st.session_state.current_report_text:
        st.warning("请先在左侧选择导入方式，并成功获取文本（如点击“开始真实解析”）！")
    else:
        # noinspection PyTypeChecker
        with st.spinner("正在唤醒 CPython 多进程计算池，首次运行需自动下载 400MB 语言模型，请耐心等待..."):
            try:
                # 构造一份假的历史基线语料，用于对照组测试
                fake_history = [
                    "大力发展高新技术产业。",
                    "稳步推进专插本招录工作。",
                    "往年重点提到了传统基建投资增速，以及能耗双控指标的严格落实。"
                ]

                # 向后端发射真实的 AI 推理请求！
                response = requests.post(
                    f"{BACKEND_URL}/analyze",
                    json={
                        "current_text": st.session_state.current_report_text,
                        "history_texts": fake_history
                    }
                )

                if response.status_code == 200:
                    # 拿到后端的真实 AI 运算结果！
                    real_response = response.json()["data"]

                    tab1, tab2, tab3, tab4 = st.tabs(
                        ["📝 排序优先级与大纲", "🔍 措辞变化分析", "✨ 新提法与词云", "⚠️ 缺失内容预警"])

                    with tab1:
                        st.subheader("高权重核心段落提取")
                        for item in real_response.get("priority_outline", []):
                            st.info(f"**权重值: {item['weight']}** \n{item['content']}")

                    with tab2:
                        st.subheader("历届政策表述变化强度测算")
                        changes = real_response.get("wording_changes", [])
                        if changes:
                            df_changes = pd.DataFrame(changes)
                            st.dataframe(df_changes, column_config={
                                "current": "本次报告表述",
                                "historical_match": "历史相似表述",
                                "change_intensity": st.column_config.ProgressColumn("变化强度", format="%f",
                                                                                    min_value=0, max_value=1)
                            }, use_container_width=True)
                        else:
                            st.write("未检测到明显的表述微调。")

                    with tab3:
                        st.subheader("首次提出核心词汇")
                        new_terms = real_response.get("new_terms", [])
                        if new_terms:
                            st.markdown(" ".join([f"`{term}`" for term in new_terms]))

                            st.subheader("政策热点词云")
                            word_freq = {str(word): max(1, 10 - i) for i, word in enumerate(new_terms)}
                            if word_freq:
                                wc = WordCloud(width=800, height=400, background_color="white",
                                               font_path="simhei.ttf").generate_from_frequencies(word_freq)
                                fig, ax = plt.subplots()
                                ax.imshow(wc, interpolation='bilinear')
                                ax.axis("off")
                                st.pyplot(fig)
                        else:
                            st.write("未提取到显著的新提法。")

                    with tab4:
                        st.subheader("潜在政策转向提示")
                        missing_content = real_response.get("missing_content", [])
                        if missing_content:
                            st.write("对比往年基线，以下重点内容本次未提及：")
                            for missing in missing_content:
                                st.error(f"📉 {missing}")
                        else:
                            st.success("核心框架保持稳定，无明显缺失。")

                else:
                    st.error(f"AI 推理报错了: {response.json().get('detail', '未知错误')}")
            except requests.exceptions.ConnectionError:
                st.error("无法连接到后端！请检查 uvicorn 是否运行。")