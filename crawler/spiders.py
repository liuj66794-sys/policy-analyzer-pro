import httpx
from urllib import robotparser
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from core.exceptions import ComplianceError  # 假设我们在 core 中定义了此异常


class OfficialPolicySpider:
    def __init__(self, user_agent: str = "PolicyAnalyzerBot/1.0 (+http://localhost)"):
        self.user_agent = user_agent
        self.parsers = {}  # 缓存各域名的 robots.txt 解析结果

    async def check_robots_compliance(self, url: str) -> bool:
        """检查目标 URL 是否允许被抓取（严格遵循 robots 协议）"""
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

        if domain not in self.parsers:
            rp = robotparser.RobotFileParser()
            rp.set_url(f"{domain}/robots.txt")
            # 异步读取 robots.txt 避免阻塞主线程
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(f"{domain}/robots.txt", timeout=5.0)
                    if response.status_code == 200:
                        rp.parse(response.text.splitlines())
                except httpx.RequestError:
                    pass  # 默认允许或按需处理网络异常
            self.parsers[domain] = rp

        return self.parsers[domain].can_fetch(self.user_agent, url)

    async def fetch_policy_report(self, url: str) -> str:
        """
        【异步 I/O 优化】:
        使用 async/await 挂起网络请求。
        在等待官方服务器响应期间，Python 主线程会切换去处理其他并发请求，
        从而在不增加线程开销的情况下极大提升爬取效率。
        """
        is_allowed = await self.check_robots_compliance(url)
        if not is_allowed:
            raise ComplianceError(f"Robots.txt 禁止抓取该链接: {url}")

        async with httpx.AsyncClient(headers={"User-Agent": self.user_agent}) as client:
            response = await client.get(url, timeout=15.0)
            response.raise_for_status()

            # 使用 BeautifulSoup 提取正文主体 (需根据具体政府网站 DOM 结构微调)
            soup = BeautifulSoup(response.text, 'html.parser')
            # 假设官方报告的正文通常包裹在 id="UCAP-CONTENT" 或 class="article-content" 中
            content_div = soup.find(id='UCAP-CONTENT') or soup.find(class_='article-content')

            if not content_div:
                # 降级策略：提取全部文本
                return soup.get_text()
            return content_div.get_text()