from __future__ import annotations
import os
import json
import time
from typing import Tuple
from dotenv import load_dotenv
from .schemas import QAExample, JudgeResult, ReflectionEntry
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM

load_dotenv()

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_llm(system_prompt: str, user_prompt: str) -> Tuple[str, int]:
    """Gọi LLM và trả về (response, token_count)"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Rẻ hơn gpt-3.5-turbo 3 lần!
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )
    content = response.choices[0].message.content
    total_tokens = response.usage.total_tokens
    return content, total_tokens


# ============ CÁC HÀM CHÍNH ============

def actor_answer(example: QAExample, attempt_id: int, agent_type: str, 
                 reflection_memory: list[str]) -> Tuple[str, int]:
    """Actor trả lời câu hỏi"""
    context_text = "\n".join([f"[{c.title}]: {c.text}" for c in example.context])
    
    reflection_hint = ""
    if reflection_memory:
        reflection_hint = f"\n\nPrevious attempts failed. Lessons learned:\n" + \
                         "\n".join(f"- {r}" for r in reflection_memory)
    
    user_prompt = f"""Question: {example.question}

Context:
{context_text}
{reflection_hint}

Provide your answer:"""
    
    response, tokens = call_llm(ACTOR_SYSTEM, user_prompt)
    
    # Extract answer from response
    answer = response
    if "Answer:" in response:
        answer = response.split("Answer:")[-1].strip()
    
    return answer, tokens

def evaluator(example: QAExample, answer: str) -> Tuple[JudgeResult, int]:
    """Evaluator đánh giá câu trả lời"""
    user_prompt = f"""Question: {example.question}
Predicted Answer: {answer}
Gold Answer: {example.gold_answer}

Evaluate and return JSON:"""
    
    response, tokens = call_llm(EVALUATOR_SYSTEM, user_prompt)
    
    try:
        result = json.loads(response)
        return JudgeResult(**result), tokens
    except:
        # Fallback: simple string matching
        from .utils import normalize_answer
        is_correct = normalize_answer(answer) == normalize_answer(example.gold_answer)
        return JudgeResult(
            score=1 if is_correct else 0,
            reason="String match evaluation",
            missing_evidence=[],
            spurious_claims=[]
        ), tokens

def reflector(example: QAExample, attempt_id: int, 
              judge: JudgeResult, answer: str) -> Tuple[ReflectionEntry, int]:
    """Reflector phân tích lỗi"""
    user_prompt = f"""Question: {example.question}
Wrong Answer: {answer}
Gold Answer: {example.gold_answer}
Evaluation: {judge.reason}

Analyze and return JSON:"""
    
    response, tokens = call_llm(REFLECTOR_SYSTEM, user_prompt)
    
    try:
        result = json.loads(response)
        return ReflectionEntry(attempt_id=attempt_id, **result), tokens
    except:
        return ReflectionEntry(
            attempt_id=attempt_id,
            failure_reason=judge.reason,
            lesson="Need to read context more carefully",
            next_strategy="Focus on all relevant passages"
        ), tokens