import asyncio
import argparse
import logging
import yaml
import sys

from src.browser import BrowserManager
from src.quiz_solver import QuizSolver


def setup_logging(level: str):
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("quiz_agent.log")
        ]
    )


async def main(url: str, config_path: str = "config.yaml", email: str = "", password: str = ""):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    setup_logging(config.get("logging", {}).get("level", "INFO"))
    logger = logging.getLogger(__name__)

    credentials = {}
    if email and password:
        credentials["microsoft"] = {"email": email, "password": password}

    logger.info(f"Starting quiz solver for: {url}")

    browser = BrowserManager(config)
    await browser.start()

    result = {"status": "failed", "url": url, "questions_solved": 0, "errors": []}

    try:
        solver = QuizSolver(browser, config)

        is_microsoft_form = "forms.office.com" in url.lower() or "forms.microsoft.com" in url.lower() or "forms.cloud.microsoft" in url.lower()

        if is_microsoft_form and credentials and credentials.get("microsoft"):
            logger.info("Step 1: Navigating to login page...")
            await browser.navigate("https://login.microsoft.com/")
            await asyncio.sleep(3)
            
            logger.info("Step 2: Logging in...")
            login_success = await solver.login_microsoft(credentials["microsoft"])
            logger.info(f"Login result: {login_success}")
            
            logger.info("Step 3: Navigating to quiz...")
            await browser.navigate(url)
            await asyncio.sleep(8)

        result = await solver.solve(url)

        logger.info(f"Result: {result}")
        print(f"Quiz completed! Status: {result['status']}")

        if result.get("errors"):
            print(f"Errors: {result['errors']}")

    except Exception as e:
        logger.error(f"Error: {e}")
        result["errors"].append(str(e))
        print(f"Quiz failed: {e}")
    finally:
        await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quiz Solver Agent")
    parser.add_argument("url", help="Quiz URL to solve")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--email", help="Email for login", default="")
    parser.add_argument("--password", help="Password for login", default="")
    args = parser.parse_args()

    asyncio.run(main(args.url, args.config, args.email, args.password))