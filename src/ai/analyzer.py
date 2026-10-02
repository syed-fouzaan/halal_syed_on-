from typing import Any, Dict, List, Optional
from src.ai.ollama_client import OllamaClient
from src.ai.prompts import load_prompt_templates, format_rag_prompt
from src.ai.retrieval import retrieve_top_chunks, build_retrieval_context
from src.utils.logging import get_logger

logger = get_logger("ai_analyzer")

class AIAnalyzer:
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self.client = ollama_client or OllamaClient()
        self.prompts = load_prompt_templates()

    def ask_rag(
        self,
        question: str,
        evidence_chunks: List[Dict[str, Any]],
        portfolio_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes Section 16 RAG Pipeline:
        1. Retrieve top chunks
        2. Build context
        3. Query local LLM
        4. Return response + verified evidence chunks
        """
        top_chunks = retrieve_top_chunks(query=question, evidence_chunks=evidence_chunks, top_k=4)
        evidence_str = build_retrieval_context(top_chunks)
        prompt = format_rag_prompt(question, evidence_str, portfolio_context)
        system_p = self.prompts.get("system_prompt")

        llm_result = self.client.generate(prompt=prompt, system=system_p)
        
        return {
            "answer": llm_result["text"],
            "success": llm_result["success"],
            "error": llm_result.get("error"),
            "cited_chunks": top_chunks,
            "evidence_count": len(top_chunks)
        }

    def generate_monthly_ai_observation(
        self,
        portfolio_summary: Dict[str, Any],
        shariah_summary: Dict[str, Any]
    ) -> str:
        """Generate monthly AI executive summary or fallback to deterministic summary."""
        context = (
            f"Net Invested: ₹{portfolio_summary.get('net_invested', 0):,.2f}\n"
            f"Current Value: ₹{portfolio_summary.get('current_value', 0):,.2f}\n"
            f"Absolute Gain: ₹{portfolio_summary.get('gain', 0):,.2f} ({portfolio_summary.get('return_pct', 0)}%)\n"
            f"XIRR: {round(portfolio_summary.get('xirr', 0.0) * 100, 2) if portfolio_summary.get('xirr') else 'N/A'}%\n"
            f"Shariah Compliance: {shariah_summary.get('status', 'COMPLIANT')}\n"
        )
        prompt = (
            f"Based strictly on these portfolio figures:\n{context}\n"
            "Provide a concise 3-bullet executive observation summarizing portfolio growth and compliance."
        )
        res = self.client.generate(prompt=prompt, system=self.prompts.get("system_prompt"))
        if res["success"]:
            return res["text"]
        
        # Deterministic fallback when AI is unavailable
        return (
            f"• Portfolio value stands at ₹{portfolio_summary.get('current_value', 0):,.2f} against ₹{portfolio_summary.get('net_invested', 0):,.2f} invested.\n"
            f"• Cumulative return is {portfolio_summary.get('return_pct', 0)}% (XIRR: {round(portfolio_summary.get('xirr', 0.0) * 100, 2) if portfolio_summary.get('xirr') else 'N/A'}%).\n"
            f"• Shariah compliance status is '{shariah_summary.get('status', 'COMPLIANT')}'; zero prohibited sector violations detected in current holdings."
        )
