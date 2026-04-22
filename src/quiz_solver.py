import logging
import asyncio
from typing import Dict, List, Optional

from .browser import BrowserManager
from .answer_finder import AnswerFinder

logger = logging.getLogger(__name__)


class QuizSolver:
    def __init__(self, browser: BrowserManager, config: dict):
        self.browser = browser
        self.config = config
        self.answer_finder = AnswerFinder()

    async def login_microsoft(self, credentials: dict) -> bool:
        logger.info("Logging into Microsoft")

        try:
            email = credentials.get("email", "")
            password = credentials.get("password", "")

            if not email or not password:
                logger.info("No credentials provided, skipping login")
                return False

            current_url = self.browser.page.url
            logger.info(f"Current URL before login: {current_url}")

            await self.browser.screenshot("login_page.png")

            email_input = None
            try:
                email_input = await self.browser.page.query_selector("input[type='email'], input[name='loginfmt'], input#i0116")
            except:
                pass
            
            if not email_input:
                try:
                    email_input = await self.browser.page.query_selector("input[type='text']")
                except:
                    pass

            if email_input:
                await email_input.fill(email)
                await self.browser.page.keyboard.press("Enter")
                await asyncio.sleep(6)

            await self.browser.screenshot("after_email.png")

            password_input = None
            try:
                password_input = await self.browser.page.query_selector("input[type='password'], input[name='passwd']")
            except:
                pass
            
            if not password_input:
                try:
                    password_input = await self.browser.page.query_selector("input#i0118")
                except:
                    pass

            if password_input:
                await password_input.fill(password)
                await self.browser.page.keyboard.press("Enter")
                await asyncio.sleep(10)

            await self.browser.screenshot("after_login.png")

            await self.browser.page.wait_for_load_state("networkidle", timeout=15000)
            await asyncio.sleep(2)

            logger.info("Microsoft login completed")
            return True

        except Exception as e:
            logger.error(f"Microsoft login error: {e}")
            return False

    async def login_google(self, credentials: dict) -> bool:
        logger.info("Logging into Google")

        try:
            email = credentials.get("email", "")
            password = credentials.get("password", "")

            if not email or not password:
                logger.info("No credentials provided, skipping login")
                return False

            await self.browser.page.goto("https://accounts.google.com/")
            await asyncio.sleep(2)

            email_input = await self.browser.page.query_selector("input[type='email'], input[type='text']")
            if email_input:
                await email_input.fill(email)
                await self.browser.page.click("div[id='identifierNext']")
                await asyncio.sleep(3)

            password_input = await self.browser.page.query_selector("input[type='password']")
            if password_input:
                await password_input.fill(password)
                await self.browser.page.click("div[id='passwordNext']")
                await asyncio.sleep(3)

            logger.info("Google login completed")
            return True

        except Exception as e:
            logger.error(f"Google login error: {e}")
            return False

    async def solve(self, url: str) -> Dict:
        result = {"status": "started", "url": url, "questions_solved": 0, "errors": []}

        try:
            await self.browser.navigate(url)
            await self.browser.wait_for_navigation()

            if "kahoot.it" in url.lower() or "kahoot.com" in url.lower():
                await self.solve_kahoot()
            elif "docs.google.com" in url.lower() or "forms.google.com" in url.lower():
                await self.solve_google_form()
            elif "forms.microsoft.com" in url.lower() or "forms.office.com" in url.lower() or "forms.cloud.microsoft" in url.lower():
                await self.solve_microsoft_form()
            else:
                await self.solve_generic()

            result["status"] = "completed"
            result["questions_solved"] = 0

        except Exception as e:
            logger.error(f"Error solving quiz: {e}")
            result["errors"].append(str(e))
            result["status"] = "failed"

        return result

    async def solve_kahoot(self):
        logger.info("Solving Kahoot quiz")
        await asyncio.sleep(2)

        try:
            start_button = await self.browser.page.query_selector("button[class*='start'], button:has-text('Start')")
            if start_button:
                await start_button.click()
                logger.info("Clicked start button")
                await asyncio.sleep(1)

            for i in range(50):
                questions = await self.answer_finder.extract_kahoot_questions(self.browser.page)
                if not questions:
                    break

                for q in questions:
                    answer_idx = await self.answer_finder.find_answer(q["question"], q["options"])
                    if answer_idx is not None and answer_idx < len(q["options"]):
                        buttons = await self.browser.page.query_selector_all("button[class*='answer']")
                        if answer_idx < len(buttons):
                            await buttons[answer_idx].click()
                            logger.info(f"Clicked answer {answer_idx}")
                            await asyncio.sleep(1)

                next_button = await self.browser.page.query_selector("button[class*='next'], button:has-text('Next')")
                if next_button:
                    await next_button.click()
                    await asyncio.sleep(1)
                else:
                    break

        except Exception as e:
            logger.error(f"Error in Kahoot solving: {e}")

    async def solve_google_form(self):
        logger.info("Solving Google Form quiz")

        try:
            for i in range(100):
                questions = await self.answer_finder.extract_google_form_questions(self.browser.page)
                if not questions:
                    break

                for q in questions:
                    answer_idx = await self.answer_finder.find_answer(q["question"], q["options"])
                    if answer_idx is not None:
                        radio_buttons = await self.browser.page.query_selector_all("div[role='radio']")
                        if answer_idx < len(radio_buttons):
                            await radio_buttons[answer_idx].click()
                            logger.info(f"Selected answer {answer_idx}")
                            await asyncio.sleep(0.5)

                next_button = await self.browser.page.query_selector("div[role='button']:has-text('Next'), div[class*='next']")
                if next_button:
                    await next_button.click()
                    await asyncio.sleep(1)
                else:
                    submit_button = await self.browser.page.query_selector("div[role='button']:has-text('Submit')")
                    if submit_button:
                        await submit_button.click()
                        logger.info("Submitted form")
                    break

        except Exception as e:
            logger.error(f"Error in Google Form solving: {e}")

    async def solve_microsoft_form(self):
        logger.info("Solving Microsoft Form quiz")

        try:
            await self.browser.page.wait_for_load_state("networkidle", timeout=20000)
            await asyncio.sleep(5)

            title = await self.browser.page.title()
            logger.info(f"Page title: {title}")

            if title == "Sign in to your account":
                logger.info("Need login, returning")
                return

            await self.browser.screenshot("quiz_page.png")

            try:
                await self.browser.page.wait_for_selector("form", timeout=10000)
            except:
                await asyncio.sleep(5)

            all_inputs = await self.browser.page.query_selector_all("input:not([type='radio']):not([type='checkbox']):not([type='submit']), textarea")
            logger.info(f"Found {len(all_inputs)} inputs total")
            
            labels = await self.browser.page.query_selector_all("label, span, h3")
            
            name = self.config.get("user", {}).get("name", "Utkarsh Yadav")
            class_section = self.config.get("user", {}).get("class_section", "29")
            roll_no = self.config.get("user", {}).get("roll_no", "2400320101209")
            
            logger.info(f"Filling: Name={name}, Class={class_section}, Roll={roll_no}")
            
            filled_count = 0
            for idx, inp in enumerate(all_inputs):
                try:
                    inp_type = await inp.get_attribute("type")
                    if inp_type in ["radio", "checkbox", "submit", "hidden", "button"]:
                        continue
                        
                    aria_label = await inp.get_attribute("aria-label")
                    placeholder = await inp.get_attribute("placeholder")
                    id_val = await inp.get_attribute("id")
                    title_val = await inp.get_attribute("title")
                    
                    combined = f"{aria_label} {placeholder} {id_val} {title_val}".lower()
                    
                    if "name" in combined or filled_count == 0:
                        await inp.fill(name)
                        logger.info(f"Filled name: {name}")
                    elif ("class" in combined or "section" in combined or "year" in combined or "semester" in combined or filled_count == 1):
                        await inp.fill(class_section)
                        logger.info(f"Filled class: {class_section}")
                    elif "roll" in combined or "reg" in combined or "id" in combined or filled_count == 2:
                        await inp.fill(roll_no)
                        logger.info(f"Filled roll: {roll_no}")
                    elif ("branch" in combined or "dept" in combined):
                        await inp.fill("CSE")
                        
                    logger.info(f"Filled input {idx}: {combined[:50]}")
                    await asyncio.sleep(0.3)
                    filled_count += 1
                except Exception as e:
                    logger.info(f"Error filling input {idx}: {e}")

            await asyncio.sleep(1)

            radio_groups = await self.browser.page.query_selector_all("div[role='radiogroup'], fieldset")
            logger.info(f"Found {len(radio_groups)} radio groups")

            for attempt in range(30):
                await asyncio.sleep(2)

                await self.browser.screenshot(f"quiz_{attempt}.png")

                radio_inputs = await self.browser.page.query_selector_all("input[type='radio']")
                logger.info(f"Attempt {attempt}: Found {len(radio_inputs)} radio inputs")

                if not radio_inputs:
                    logger.info("No radio inputs, looking for submit button...")
                    all_btns = await self.browser.page.query_selector_all("button, input[type='submit']")
                    for btn in all_btns:
                        try:
                            btn_text = await btn.inner_text() if hasattr(btn, 'inner_text') else await btn.get_attribute("value") or ""
                        except:
                            btn_text = ""
                        if "Submit" in str(btn_text):
                            await btn.click()
                            logger.info("Submitted quiz!")
                            break
                    break

                first_options = radio_inputs[:4]
                for idx, radio in enumerate(first_options):
                    try:
                        await radio.click()
                        logger.info(f"Clicked option {idx}")
                        await asyncio.sleep(0.3)
                    except:
                        pass

                all_btns = await self.browser.page.query_selector_all("button")
                clicked_next = False
                for btn in all_btns:
                    btn_text = await btn.inner_text()
                    if "Next" in str(btn_text):
                        await btn.click()
                        logger.info("Clicked Next")
                        clicked_next = True
                        break
                
                if not clicked_next:
                    for btn in all_btns:
                        btn_text = await btn.inner_text()
                        if "Submit" in str(btn_text):
                            await btn.click()
                            logger.info("Submitted")
                            break
                    break

        except Exception as e:
            logger.error(f"Error in Microsoft Form solving: {e}")

            for i in range(100):
                questions = await self.answer_finder.extract_microsoft_form_questions(self.browser.page)
                if not questions:
                    logger.info(f"No questions found on page {i+1}")
                    break

                logger.info(f"Found {len(questions)} questions")

                for q in questions:
                    answer_idx = await self.answer_finder.find_answer(q["question"], q["options"])
                    if answer_idx is not None:
                        radio_inputs = await self.browser.page.query_selector_all("input[type='radio']")
                        if answer_idx < len(radio_inputs):
                            await radio_inputs[answer_idx].click()
                            logger.info(f"Selected answer {answer_idx}")
                            await asyncio.sleep(0.5)

                next_button = await self.browser.page.query_selector("button[data-automation-id='nextButton']")
                if next_button:
                    await next_button.click()
                    await asyncio.sleep(1)
                else:
                    submit_button = await self.browser.page.query_selector("button[data-automation-id='submitButton']")
                    if submit_button:
                        await submit_button.click()
                        logger.info("Submitted form")
                    break

        except Exception as e:
            logger.error(f"Error in Microsoft Form solving: {e}")

    async def solve_generic(self):
        logger.info("Solving generic quiz")
        await asyncio.sleep(1)

        try:
            await self.browser.page.wait_for_load_state("domcontentloaded")
            forms = await self.browser.page.query_selector_all("form")
            for form in forms:
                inputs = await form.query_selector_all("input[type='radio'], input[type='checkbox']")
                buttons = await form.query_selector_all("button[type='submit'], input[type='submit']")

                for inp in inputs:
                    await inp.click()
                    await asyncio.sleep(0.3)

                if buttons:
                    await buttons[0].click()
                    logger.info("Submitted form")

        except Exception as e:
            logger.error(f"Error in generic solving: {e}")