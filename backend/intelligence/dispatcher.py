"""
dispatcher.py — Dual-Path Hybrid Intelligence Dispatcher.

Coordinates:
  - Path A: Direct Analytical Responses (Instant, 0 LLM Tokens, 0 Inference Latency)
  - Path B: LLM-Assisted Responses (Compact Verified Facts via Ollama Qwen3.5 4B)
Tracks performance metrics and manages conversation memory.
"""

from typing import Any
import time
import httpx
import logging
from .schema import AcademicSchema
from .engine import AcademicQueryEngine, QueryResult
from .planner import QueryPlanner
from .memory import ConversationMemory

logger = logging.getLogger(__name__)


def sanitize_llm_response(text: str) -> str:
    """Strip chain-of-thought, <think> tags, or 'Thinking Process:' from LLM output."""
    import re
    if not text:
        return ""

    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    if "Thinking Process:" in cleaned:
        for marker in ["**Final Response:**", "Final Response:", "**Answer:**", "Answer:", "Output:", "**Output:**"]:
            if marker in cleaned:
                cleaned = cleaned.split(marker)[-1].strip()
                break
        else:
            parts = cleaned.split("Thinking Process:")
            after_thinking = parts[1]
            paragraphs = after_thinking.split("\n\n")
            conclusion_paras = [
                p.strip() for p in paragraphs
                if p.strip() and not re.match(r'^(\d+\.|\*|\-|\bAnalyze\b|\bScan\b|\bExamine\b|\bDetermine\b|\bFormulate\b|\bDraft\b|\bReview\b)', p.strip(), re.IGNORECASE)
            ]
            if conclusion_paras:
                cleaned = "\n\n".join(conclusion_paras).strip()
            elif parts[0].strip():
                cleaned = parts[0].strip()

    cleaned = re.sub(r'\s*cw\s*$', '', cleaned)
    # Normalize inline bullet points if model bundled them onto one line
    cleaned = re.sub(r'([.!?:\w\)])\s+([*•\-]\s+)', r'\1\n\n\2', cleaned, count=1)
    cleaned = re.sub(r'([.!?:\w\)])\s+([*•\-]\s+)', r'\1\n\2', cleaned)
    cleaned = re.sub(r'([.!?:\w\)])\s+(\d+\.\s+)', r'\1\n\2', cleaned)
    return cleaned.strip()


class HybridIntelligenceDispatcher:
    """Orchestrates query planning, Python execution, and selective LLM dispatching."""

    def __init__(
        self,
        raw_results: list[dict],
        llm_api_base: str = "http://localhost:11434/v1",
        llm_model: str = "qwen3.5:4b",
        llm_api_key: str = "ollama",
        llm_timeout: float = 180.0,
        memory: ConversationMemory | None = None
    ):
        self.raw_results = raw_results or []
        self.llm_api_base = llm_api_base
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key
        self.llm_timeout = llm_timeout

        self.schema = AcademicSchema(self.raw_results)
        self.engine = AcademicQueryEngine(self.raw_results)
        self.planner = QueryPlanner()
        self.memory = memory if memory is not None else ConversationMemory()

    async def process_query(self, user_question: str) -> dict[str, Any]:
        """
        Executes query along the optimal path:
          - Path A (Direct): Instant Python evaluation for clear factual questions.
          - Path B (LLM): Compact verified facts passed to Qwen 3.5 4B for pedagogical explanations.
        """
        t_start = time.perf_counter()

        # Step 1: Query Planning
        t_plan_start = time.perf_counter()
        plan, is_direct_path, intent = self.planner.plan_query(
            user_question, self.schema, self.memory
        )
        t_plan_ms = round((time.perf_counter() - t_plan_start) * 1000, 2)

        # Step 2: Safe Python Execution
        query_result: QueryResult = self.engine.execute(plan)
        t_exec_ms = query_result.execution_time_ms

        # Step 3: Dispatch Decision
        if is_direct_path and query_result.success:
            # ── PATH A: Direct Analytical Response (Instant, 0 LLM Tokens) ──
            final_answer = query_result.summary_markdown
            t_total_ms = round((time.perf_counter() - t_start) * 1000, 2)

            self.memory.record_turn(
                user_query=user_question,
                assistant_response=final_answer,
                query_type=intent,
                subject_code=plan.subject_code,
                gender="Female" if any(f.val == "Female" for f in plan.filters) else ("Male" if any(f.val == "Male" for f in plan.filters) else None)
            )

            return {
                "answer": final_answer,
                "path": "path_a_direct",
                "intent": intent,
                "tokens_consumed": 0,
                "latency_ms": {
                    "planning": t_plan_ms,
                    "execution": t_exec_ms,
                    "inference": 0.0,
                    "total": t_total_ms
                },
                "verified_facts_count": len(query_result.verified_facts)
            }

        # ── PATH B: LLM-Assisted Response (Compact Verified Facts Context) ──
        t_infer_start = time.perf_counter()
        verified_context_lines = [
            f"### Verified Academic Facts for Query: '{user_question}'"
        ]
        for fact in query_result.verified_facts[:20]:
            verified_context_lines.append(f"* {fact}")
        verified_context_str = "\n".join(verified_context_lines)

        system_prompt = (
            "You are an academic intelligence assistant for student examination results. "
            "You are provided with pre-calculated, verified academic facts and statistics.\n\n"
            "STRICT GUIDELINES:\n"
            "1. Answer the question directly, concisely, and accurately using ONLY the verified facts provided below.\n"
            "2. Do NOT show any 'Thinking Process:', chain of thought, or step-by-step calculations.\n"
            "3. Provide ONLY the final answer and a short natural-language explanation.\n"
            "4. Format your answer with clean Markdown:\n"
            "   - Separate paragraphs with a blank line.\n"
            "   - When listing student details or statistics, put EACH attribute or item on its own new line starting with '* ' or '- '.\n"
            "   - Never bunch multiple bullet points onto the same line.\n"
            "   - Use **bold** for key names, register numbers, ranks, and totals.\n"
            "5. If there is a tie, mention all tied students.\n"
            "6. Never guess, invent, or recalculate totals or statistics.\n\n"
            f"{verified_context_str}"
        )

        api_base = self.llm_api_base.rstrip("/")
        if api_base.endswith("/chat/completions"):
            endpoint = api_base
        elif api_base.endswith("/v1"):
            endpoint = f"{api_base}/chat/completions"
        else:
            endpoint = f"{api_base}/v1/chat/completions"

        headers = {"Content-Type": "application/json"}
        if self.llm_api_key:
            headers["Authorization"] = f"Bearer {self.llm_api_key}"

        messages = [{"role": "system", "content": system_prompt}]
        # Append up to 2 prior exchanges for conversational continuity
        messages.extend(self.memory.get_compact_history())
        messages.append({"role": "user", "content": user_question})

        payload = {
            "model": self.llm_model,
            "messages": messages,
            "temperature": 0.1,
            "keep_alive": "15m"
        }

        try:
            async with httpx.AsyncClient(timeout=self.llm_timeout) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                raw_answer = ""
                choices = data.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {})
                    raw_answer = msg.get("content") or msg.get("reasoning", "")
                else:
                    raw_answer = data.get("answer") or str(data)

                final_answer = sanitize_llm_response(raw_answer)
                if not final_answer:
                    final_answer = query_result.summary_markdown

        except Exception as e:
            logger.warning(f"LLM inference encountered error ({e}); falling back to verified analytical summary.")
            final_answer = query_result.summary_markdown

        t_infer_ms = round((time.perf_counter() - t_infer_start) * 1000, 2)
        t_total_ms = round((time.perf_counter() - t_start) * 1000, 2)

        self.memory.record_turn(
            user_query=user_question,
            assistant_response=final_answer,
            query_type=intent
        )

        # Estimate prompt + output tokens (rough heuristic: 1 token ~ 4 chars)
        est_tokens = len(system_prompt + user_question + final_answer) // 4

        return {
            "answer": final_answer,
            "path": "path_b_llm",
            "intent": intent,
            "tokens_consumed": est_tokens,
            "latency_ms": {
                "planning": t_plan_ms,
                "execution": t_exec_ms,
                "inference": t_infer_ms,
                "total": t_total_ms
            },
            "verified_facts_count": len(query_result.verified_facts)
        }
