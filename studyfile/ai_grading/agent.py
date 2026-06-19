import json
import logging
import re

from .client import get_client
from .client import get_model
from .tools import TOOLS
from .tools import execute_tool

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 10

SYSTEM_PROMPT = """You are an AI teaching assistant that evaluates student assignment submissions.

You will be given:
1. The assignment title and description
2. The student's submission file(s)
3. Any optional comment from the student

Your task:
- Carefully read and analyze the student's work
- Evaluate it against the assignment requirements
- Provide a grade (0-100) and detailed feedback

Use the available tools to read the submission files. For ZIP archives, explore the contents and read relevant files.

IMPORTANT: If the assignment description contains a link to an Affine document (URLs like https://docs.ravonzz174.ru/workspace/...), use the read_affine tool to fetch and read the full assignment requirements from that document BEFORE evaluating the submission.

When you are ready to provide your evaluation, respond with a JSON object in the following format (and ONLY the JSON, nothing else):

{
    "grade": <number 0-100>,
    "feedback": "<detailed feedback in Russian explaining the grade>"
}

Important:
- Be fair and constructive in your feedback
- Point out both strengths and areas for improvement
- Base your evaluation strictly on the assignment requirements
- Respond in Russian
- Your final response must be valid JSON with grade and feedback fields"""


def run_grading_agent(
    assignment_title: str,
    assignment_description: str,
    submission_file_path: str,
    student_comment: str = "",
) -> dict:
    client = get_client()
    model = get_model()

    user_message = f"""## Assignment

**Title:** {assignment_title}

**Description:**
{assignment_description}

## Student Submission

**File:** {submission_file_path}
"""

    if student_comment:
        user_message += f"\n**Student comment:**\n{student_comment}\n"

    user_message += "\nPlease read the submission file(s) using the available tools, analyze the work, and provide your evaluation."

    messages = [{"role": "user", "content": user_message}]

    for iteration in range(MAX_ITERATIONS):
        logger.info("AI grading agent iteration %d", iteration + 1)

        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return _parse_final_response(response)

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info("Agent calling tool: %s", block.name)
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})
            continue

        logger.warning("Unexpected stop_reason: %s", response.stop_reason)
        break

    logger.error("AI grading agent exceeded max iterations")
    return {
        "grade": None,
        "feedback": "Ошибка: агент превысил максимальное количество итераций.",
    }


def _parse_final_response(response) -> dict:
    for block in response.content:
        if block.type == "text":
            text = block.text.strip()
            
            # Пробуем распарсить весь текст как JSON
            try:
                data = json.loads(text)
                grade = data.get("grade")
                feedback = data.get("feedback", "")
                if grade is not None:
                    grade = float(grade)
                    if grade < 0 or grade > 100:
                        grade = max(0, min(100, grade))
                return {"grade": grade, "feedback": feedback}
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
            
            # Ищем JSON в markdown code block
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    grade = data.get("grade")
                    feedback = data.get("feedback", "")
                    if grade is not None:
                        grade = float(grade)
                        if grade < 0 or grade > 100:
                            grade = max(0, min(100, grade))
                    return {"grade": grade, "feedback": feedback}
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
            
            # Ищем любой JSON объект в тексте
            json_match = re.search(r'\{[^{}]*"grade"[^{}]*\}', text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    grade = data.get("grade")
                    feedback = data.get("feedback", "")
                    if grade is not None:
                        grade = float(grade)
                        if grade < 0 or grade > 100:
                            grade = max(0, min(100, grade))
                    return {"grade": grade, "feedback": feedback}
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass

    return {
        "grade": None,
        "feedback": "Ошибка: не удалось получить оценку от AI агента.",
    }
