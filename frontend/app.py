import streamlit as st
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import requests

# 预设的 FastAPI 后端地址
BACKEND_URL = "http://localhost:8000/api/v1/policy"

# ==========================================
# 顶层 UI 配置与全局免责
# ==========================================
st.set_page_config(page_title="中国政策报告智能分析系统", layout="wide")
st.warning("⚠️ **合规免责声明**：本软件分析结果仅供参考，决策请以官方发布稿为准。全流程不存储用户数据。")
st.title("🏛️ 政策报告智能分析引擎 (Pro 最终修复版)")

# ==========================================
# 状态缓存初始化 (解决内容消失与状态不协调的核心)
# ==========================================
state_keys = {
    "current_single_text": "",
    "single_analysis_result": None,
    "compare_analysis_result": None,
    "compare_files_info": ("", "")
}
for key, value in state_keys.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================
# 通用工具函数 (资深开发规范：DRY原则)
# ==========================================
def render_wordcloud(terms: list):
    """封装词云渲染逻辑"""
    try:
        if not terms:
            st.info("数据量不足，无法生成词云。")
            return
        word_freq = {str(word): max(1, 10 - i) for i, word in enumerate(terms)}
        wc = WordCloud(width=800, height=400, background_color="white",
                       font_path="simhei.ttf").generate_from_frequencies(word_freq)
        fig, ax = plt.subplots()
        ax.imshow(wc, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)
    except Exception as err:
        st.warning(f"词云渲染失败，请检查根目录 simhei.ttf。详情: {err}")


def generate_markdown_report(data: dict, file_old: str, file_new: str) -> str:
    """自动生成精美 Markdown 简报"""
    md = f"# 🏛️ 政策变迁深度比对简报\n\n"
    md += f"**基准文档**: {file_old}  \n**对比文档**: {file_new}\n\n---\n"
    md += "## 📊 核心指标概览\n"
    md += f"- **语义变动点**: {len(data.get('wording_changes', []))} 处\n"
    md += f"- **新增核心词**: {len(data.get('new_terms', []))} 个\n"
    md += f"- **缺失与弱化**: {len(data.get('missing_content', []))} 项\n\n---\n"

    md += "## 🔄 核心表述演变轨迹\n"
    for change in data.get('wording_changes', []):
        md += f"* **旧版**: {change.get('historical_match', '')}  \n"
        md += f"  **新版**: {change.get('current', '')} (强度: {change.get('change_intensity', 0):.2f})\n\n"

    md += "## ✨ 新增核心提法\n"
    md += "> " + "、".join(data.get('new_terms', [])) + "\n\n"

    md += "## 📉 动态删减与转向预警\n"
    for m in data.get('missing_content', []):
        md += f"- {m}\n"

    md += "\n\n---\n*由 Policy-Analyzer-Pro 智能引擎生成*"
    return md


def display_analysis_results(data: dict, is_comparison=False):
    """统一的分析结果可视化面板"""
    if is_comparison:
        c1, c2, c3 = st.columns(3)
        c1.metric("语义变动点", f"{len(data.get('wording_changes', []))} 处")
        c2.metric("新增关键词", f"{len(data.get('new_terms', []))} 个")
        c3.metric("弱化/删减项", f"{len(data.get('missing_content', []))} 项")
        st.markdown("---")

    t1, t2, t3, t4 = st.tabs(["📝 核心大纲", "🔍 措辞变化", "✨ 新提法/词云", "⚠️ 删减/弱化"])

    with t1:
        st.subheader("核心议题提取")
        outline = data.get("priority_outline", [])
        if outline:
            for item in outline:
                st.info(f"**权重: {item['weight']}** \n{item['content']}")
        else:
            st.write("未检测到显著议题。")

    with t2:
        st.subheader("表述演变细节")
        changes = data.get("wording_changes", [])
        if changes:
            df = pd.DataFrame(changes)
            st.dataframe(df, column_config={
                "current": "本次/新稿表述",
                "historical_match": "往年/旧稿匹配",
                "change_intensity": st.column_config.ProgressColumn("语义偏移强度", min_value=0, max_value=1)
            }, use_container_width=True)
        else:
            st.write("框架保持一致。")

    with t3:
        st.subheader("新增核心提法")
        terms = data.get("new_terms", [])
        if terms:
            st.markdown(" ".join([f"`{t}`" for t in terms]))
            render_wordcloud(terms)
        else:
            st.write("未发现显著新词。")

    with t4:
        st.subheader("内容转向监测")
        missing = data.get("missing_content", [])
        if missing:
            # 根据真实算法输出调整颜色级别
            if any("删减" in str(m) for m in missing):
                st.error("❗ 监测到关键议题被移除或大幅弱化：")
                for m in missing: st.markdown(f"* {m}")
            else:
                for m in missing: st.warning(f"📉 {m}")
        else:
            st.success("政策延续性良好。")


# ==========================================
# 顶层导航页签
# ==========================================
main_tabs = st.tabs(["🎯 单篇深度分析", "⚖️ 历届变迁对比"])

# ==========================================
# 功能一：单篇分析
# ==========================================
with main_tabs[0]:
    st.subheader("数据导入")
    mode = st.radio("导入方式", ["内置 Demo", "URL 抓取", "文件解析"], horizontal=True, key="s_mode")

    col_in, col_ctrl = st.columns([3, 1])
    with col_in:
        if mode == "内置 Demo":
            st.info("已准备好默认测试语料。")
            if st.button("🚀 加载数据"):
                st.session_state.current_single_text = "深入推进教育强省建设。优化职业教育，扩大高质量专升本招生规模。坚持把高质量充分就业作为经济社会发展的优先目标。培育新质生产力，加快建设现代化产业体系。"
                st.success("加载成功！")
        elif mode == "URL 抓取":
            url = st.text_input("请输入官方报告网页链接")
            if st.button("🚀 开始抓取"):
                # noinspection PyTypeChecker
                with st.spinner("网络抓取中..."):
                    res = requests.post(f"{BACKEND_URL}/fetch", json={"url": url})
                    if res.status_code == 200:
                        st.session_state.current_single_text = res.json()["data"]["text"]
                        st.success("抓取并预处理完成！")
        elif mode == "文件解析":
            up = st.file_uploader("支持 PDF/DOCX/TXT", type=['pdf', 'docx', 'txt'], key="s_up")
            if up and st.button("🚀 开始解析"):
                # noinspection PyTypeChecker
                with st.spinner("正在提取文本..."):
                    files = {"file": (up.name, up.getvalue())}
                    res = requests.post(f"{BACKEND_URL}/upload", files=files)
                    if res.status_code == 200:
                        st.session_state.current_single_text = res.json()["data"]["text"]
                        st.success("解析成功！")

    with col_ctrl:
        if st.button("🧹 重置分析结果", use_container_width=True):
            st.session_state.single_analysis_result = None
            st.rerun()

    st.markdown("---")
    if st.button("🔥 启动 AI 核心分析引擎", type="primary", use_container_width=True):
        if st.session_state.current_single_text:
            # noinspection PyTypeChecker
            with st.spinner("多进程子进程正在进行张量计算..."):
                response = requests.post(f"{BACKEND_URL}/analyze",
                                         json={"current_text": st.session_state.current_single_text})
                if response.status_code == 200:
                    st.session_state.single_analysis_result = response.json()["data"]
        else:
            st.warning("请先加载数据！")

    if st.session_state.single_analysis_result:
        display_analysis_results(st.session_state.single_analysis_result)

# ==========================================
# 功能二：双篇对比 (含导出)
# ==========================================
with main_tabs[1]:
    st.subheader("变迁比对控制台")
    c_o, c_n = st.columns(2)
    with c_o:
        f_o = st.file_uploader("📂 基准文档 (往年/旧稿)", type=['pdf', 'docx', 'txt'], key="c_o")
    with c_n:  # 【关键修复】：这里已修改为正确的 c_n
        f_n = st.file_uploader("📂 对比文档 (今年/新稿)", type=['pdf', 'docx', 'txt'], key="c_n")

    if f_o and f_n:
        if st.button("⚖️ 启动双篇深度对比", type="primary", use_container_width=True):
            # noinspection PyTypeChecker
            with st.spinner("正在执行 TextRank 关键词密度比对..."):
                try:
                    files = {"file_old": (f_o.name, f_o.getvalue()), "file_new": (f_n.name, f_n.getvalue())}
                    res = requests.post(f"{BACKEND_URL}/compare", files=files)
                    if res.status_code == 200:
                        st.session_state.compare_analysis_result = res.json()["data"]["analysis"]
                        st.session_state.compare_files_info = (f_o.name, f_n.name)
                except Exception as e:
                    st.error(f"分析失败: {e}")

    if st.session_state.compare_analysis_result:
        display_analysis_results(st.session_state.compare_analysis_result, is_comparison=True)

        st.markdown("### 📥 成果导出")
        report = generate_markdown_report(st.session_state.compare_analysis_result,
                                          st.session_state.compare_files_info[0],
                                          st.session_state.compare_files_info[1])
        st.download_button("📄 下载政策对比深度简报 (.md)", data=report, file_name="Report.md", type="primary")
