import logging
import re
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class AnswerFinder:
    def __init__(self):
        pass

    async def find_answer(self, question: str, options: List[str]) -> Optional[int]:
        logger.info(f"Finding answer for: {question[:50]}...")
        return None

    async def extract_questions(self, html: str) -> List[Dict]:
        questions = []
        return questions

    async def extract_google_form_questions(self, page) -> List[Dict]:
        questions = []
        try:
            question_blocks = await page.query_selector_all("div[aria-label]")

            for block in question_blocks:
                aria_label = await block.get_attribute("aria-label")
                if aria_label and "?" in aria_label:
                    question_text = aria_label

                    options = await block.query_selector_all("div[role='radio']")
                    option_list = []
                    for opt in options:
                        label = await opt.get_attribute("aria-label")
                        if label:
                            option_list.append(label)

                    if option_list:
                        questions.append({
                            "question": question_text,
                            "options": option_list,
                            "type": "radio"
                        })
        except Exception as e:
            logger.error(f"Error extracting Google Form questions: {e}")

        return questions

    async def extract_kahoot_questions(self, page) -> List[Dict]:
        questions = []
        try:
            question_blocks = await page.query_selector_all("div[class*='question']")

            for block in question_blocks:
                question_text_el = await block.query_selector("h2[class*='question'], span[class*='question']")
                if question_text_el:
                    question_text = await question_text_el.inner_text()

                    answer_options = await block.query_selector_all("button[class*='answer']")
                    option_list = []
                    for opt in answer_options:
                        text = await opt.inner_text()
                        if text:
                            option_list.append(text)

                    if question_text and option_list:
                        questions.append({
                            "question": question_text,
                            "options": option_list,
                            "type": "kahoot"
                        })
        except Exception as e:
            logger.error(f"Error extracting Kahoot questions: {e}")

        return questions

    async def extract_microsoft_form_questions(self, page) -> List[Dict]:
        questions = []
        try:
            question_blocks = await page.query_selector_all("div[data-automation-id]")

            for block in question_blocks:
                block_attr = await block.get_attribute("data-automation-id")
                if "question" in str(block_attr).lower() or "item" in str(block_attr).lower():
                    question_text_el = await block.query_selector("div[role='heading'], span[data-automation-id*='question']")
                    if question_text_el:
                        question_text = await question_text_el.inner_text()

                        options = await block.query_selector_all("input[type='radio'], input[type='checkbox']")
                        option_list = []
                        for opt in options:
                            label = await opt.get_attribute("aria-label")
                            if label:
                                option_list.append(label)

                        if question_text:
                            questions.append({
                                "question": question_text,
                                "options": option_list,
                                "type": "radio"
                            })
        except Exception as e:
            logger.error(f"Error extracting Microsoft Form questions: {e}")

        return questions