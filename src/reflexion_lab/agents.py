from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Literal
from .schemas import AttemptTrace, QAExample, ReflectionEntry, RunRecord
from .llm_runtime import actor_answer, evaluator, reflector
from .utils import normalize_answer


# ============ BONUS: Memory Compression ============
def compress_memory(memory: list[str], max_items: int = 3) -> list[str]:
    """
    BONUS FEATURE: memory_compression
    Nen reflection memory khi qua dai de tiet kiem token
    Chi giu lai cac bai hoc quan trong nhat (moi nhat)
    """
    if len(memory) <= max_items:
        return memory
    # Giu lai max_items bai hoc gan nhat (co gia tri nhat)
    return memory[-max_items:]


# ============ BONUS: Adaptive Max Attempts ============
def get_adaptive_max_attempts(difficulty: str, base_attempts: int = 3) -> int:
    """
    BONUS FEATURE: adaptive_max_attempts
    Tu dong dieu chinh so lan thu dua tren do kho cau hoi
    - Easy: it lan thu hon (2)
    - Medium: trung binh (3)
    - Hard: nhieu lan thu hon (4)
    """
    difficulty_multiplier = {
        "easy": 0.67,    # 2 attempts
        "medium": 1.0,   # 3 attempts  
        "hard": 1.33     # 4 attempts
    }
    multiplier = difficulty_multiplier.get(difficulty, 1.0)
    return max(1, round(base_attempts * multiplier))


@dataclass
class BaseAgent:
    agent_type: Literal["react", "reflexion"]
    max_attempts: int = 1
    use_adaptive_attempts: bool = False  # BONUS: adaptive_max_attempts
    use_memory_compression: bool = False  # BONUS: memory_compression
    
    def run(self, example: QAExample) -> RunRecord:
        reflection_memory: list[str] = []
        reflections: list[ReflectionEntry] = []
        traces: list[AttemptTrace] = []
        final_answer = ""
        final_score = 0
        
        # BONUS: Adaptive max attempts based on difficulty
        if self.use_adaptive_attempts and self.agent_type == "reflexion":
            actual_max_attempts = get_adaptive_max_attempts(example.difficulty, self.max_attempts)
        else:
            actual_max_attempts = self.max_attempts
        
        for attempt_id in range(1, actual_max_attempts + 1):
            start_time = time.time()
            
            # BONUS: Memory compression truoc khi gui cho Actor
            compressed_memory = reflection_memory
            if self.use_memory_compression and len(reflection_memory) > 3:
                compressed_memory = compress_memory(reflection_memory, max_items=3)
            
            answer, actor_tokens = actor_answer(example, attempt_id, self.agent_type, compressed_memory)
            judge, eval_tokens = evaluator(example, answer)
            
            latency_ms = int((time.time() - start_time) * 1000)
            token_estimate = actor_tokens + eval_tokens
            
            trace = AttemptTrace(
                attempt_id=attempt_id, 
                answer=answer, 
                score=judge.score, 
                reason=judge.reason, 
                token_estimate=token_estimate, 
                latency_ms=latency_ms
            )
            final_answer = answer
            final_score = judge.score
            
            if judge.score == 1:
                traces.append(trace)
                break
            
            # Logic Reflexion: Phan tich loi va hoc tu sai lam
            if self.agent_type == "reflexion" and attempt_id < actual_max_attempts:
                reflection, reflect_tokens = reflector(
                    example, attempt_id, judge, answer
                )
                reflection_memory.append(reflection.next_strategy)
                reflections.append(reflection)
                trace.reflection = reflection
                trace.token_estimate += reflect_tokens
            
            traces.append(trace)
        
        total_tokens = sum(t.token_estimate for t in traces)
        total_latency = sum(t.latency_ms for t in traces)
        failure_mode = self._detect_failure_mode(example, final_answer, final_score)
        
        return RunRecord(
            qid=example.qid, 
            question=example.question, 
            gold_answer=example.gold_answer, 
            agent_type=self.agent_type, 
            predicted_answer=final_answer, 
            is_correct=bool(final_score), 
            attempts=len(traces), 
            token_estimate=total_tokens, 
            latency_ms=total_latency, 
            failure_mode=failure_mode, 
            reflections=reflections, 
            traces=traces
        )
    
    def _detect_failure_mode(self, example: QAExample, answer: str, score: int) -> Literal["none", "entity_drift", "incomplete_multi_hop", "wrong_final_answer", "looping", "reflection_overfit"]:
        """Phat hien loai loi cu the de phan tich"""
        if score == 1:
            return "none"
        
        pred = normalize_answer(answer)
        gold = normalize_answer(example.gold_answer)
        
        # Kiem tra cac loai loi
        # 1. Entity drift: cau tra loi chua entity khac hoan toan
        if len(set(pred.split()) & set(gold.split())) == 0:
            return "entity_drift"
        
        # 2. Incomplete multi-hop: cau tra loi chi hoan thanh 1 phan
        if any(word in pred for word in gold.split()[:1]) and pred != gold:
            return "incomplete_multi_hop"
        
        # 3. Looping: tra loi giong het cau hoi
        if normalize_answer(example.question)[:20] in pred:
            return "looping"
        
        # 4. Mac dinh: wrong final answer
        return "wrong_final_answer"


class ReActAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_type="react", max_attempts=1)


class ReflexionAgent(BaseAgent):
    def __init__(self, max_attempts: int = 3, use_adaptive: bool = True, use_compression: bool = True) -> None:
        super().__init__(
            agent_type="reflexion", 
            max_attempts=max_attempts,
            use_adaptive_attempts=use_adaptive,  # BONUS: bat adaptive_max_attempts
            use_memory_compression=use_compression  # BONUS: bat memory_compression
        )
