import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, Playwright

logger = logging.getLogger(__name__)


class BrowserManager:
    def __init__(self, config: dict):
        self.config = config
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def start(self):
        self.playwright = await async_playwright().start()
        headless = self.config.get("browser", {}).get("headless", False)
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.page = await self.browser.new_page()
        logger.info("Browser started")

    async def navigate(self, url: str):
        if self.page:
            await self.page.goto(url)
            logger.info(f"Navigated to {url}")

    async def get_html(self) -> str:
        if self.page:
            return await self.page.content()
        return ""

    async def click_selector(self, selector: str):
        if self.page:
            await self.page.click(selector)
            logger.info(f"Clicked {selector}")

    async def fill_input(self, selector: str, value: str):
        if self.page:
            await self.page.fill(selector, value)
            logger.info(f"Filled {selector} with {value}")

    async def wait_for_selector(self, selector: str, timeout: int = 30000):
        if self.page:
            await self.page.wait_for_selector(selector, timeout=timeout)

    async def wait_for_navigation(self, timeout: int = 30000):
        if self.page:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")

    async def screenshot(self, path: str):
        if self.page:
            await self.page.screenshot(path=path)