def macro_compliance_prompt(rule_text: str, context_block: str) -> str:
    """
    Returns a prompt for flow-level macro compliance reasoning.
    """
    return (
        f"Given these code summaries and the regulatory requirement, determine if the overall flow satisfies the rule. "
        f"Analyze order, dependencies, and missing steps. Cite evidence only from provided summaries.\n"
        f"Regulatory requirement: {rule_text}\n"
        f"Code summaries:\n{context_block}\n"
        f"Respond with a verdict and explanation."
    )
"""
LLM service for code analysis and compliance reasoning.
"""
from typing import Any, Optional

from loguru import logger
from openai import AsyncAzureOpenAI, AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.exceptions import LLMProviderError

settings = get_settings()


class LLMService:
    """Unified LLM service supporting Azure OpenAI and OpenAI."""

    def __init__(self):
        self.provider = settings.llm_provider
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

        if self.provider == "azure":
            if not settings.azure_openai_endpoint or not settings.azure_openai_key:
                raise LLMProviderError("Azure OpenAI credentials not configured")

            self.client = AsyncAzureOpenAI(
                api_key=settings.azure_openai_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint,
            )
            self.model = settings.azure_openai_deployment_llm
            logger.info(f"Initialized Azure OpenAI LLM: {self.model}")

        elif self.provider == "openai":
            if not settings.openai_api_key:
                raise LLMProviderError("OpenAI API key not configured")

            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = "gpt-4o-mini"
            logger.info(f"Initialized OpenAI LLM: {self.model}")

        else:
            raise LLMProviderError(f"Unknown provider: {self.provider}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate completion from messages.

        Args:
            messages: Chat messages (system, user, assistant)
            temperature: Sampling temperature (overrides default)
            max_tokens: Max tokens (overrides default)

        Returns:
            Generated text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )

            content = response.choices[0].message.content
            logger.debug(f"LLM generated {len(content)} chars")
            return content

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise LLMProviderError(f"Failed to generate completion: {e}")

    async def generate_code_summary(self, code: str, language: str, file_path: str) -> str:
        """
        Generate natural language summary of code chunk.

        Args:
            code: Code snippet
            language: Programming language
            file_path: File path context

        Returns:
            Natural language summary
        """
        from app.prompts.templates import CODE_SUMMARY_PROMPT

        messages = [
            {"role": "system", "content": CODE_SUMMARY_PROMPT["system"]},
            {
                "role": "user",
                "content": CODE_SUMMARY_PROMPT["user"].format(
                    language=language, file_path=file_path, code=code
                ),
            },
        ]

        return await self.generate(messages, temperature=0.1, max_tokens=300)

    async def analyze_compliance(
        self,
        rule_text: str,
        code_text: str,
        file_path: str,
        start_line: int,
        end_line: int,
        language: str,
    ) -> dict[str, Any]:
        """
        Analyze code compliance against a rule.

        Args:
            rule_text: Compliance rule in natural language
            code_text: Code snippet to analyze
            file_path: File path
            start_line: Start line number
            end_line: End line number
            language: Programming language

        Returns:
            Compliance analysis result with verdict, severity, explanation, remediation
        """
        from app.prompts.templates import COMPLIANCE_ANALYSIS_PROMPT

        messages = [
            {"role": "system", "content": COMPLIANCE_ANALYSIS_PROMPT["system"]},
            {
                "role": "user",
                "content": COMPLIANCE_ANALYSIS_PROMPT["user"].format(
                    rule_text=rule_text,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    language=language,
                    code_text=code_text,
                ),
            },
        ]

        response = await self.generate(messages, temperature=0.1, max_tokens=1500)

        # Parse structured response (expects JSON)
        try:
            import json

            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON, returning raw text")
            return {
                "verdict": "unknown",
                "severity": "medium",
                "severity_score": 5.0,
                "explanation": response,
                "evidence": None,
                "remediation": None,
            }

    async def generate_scan_summary(self, violations: list[dict[str, Any]]) -> str:
        """
        Generate executive summary of scan results.

        Args:
            violations: List of violations

        Returns:
            Summary text
        """
        from app.prompts.templates import SCAN_SUMMARY_PROMPT

        # Prepare violation summary
        violation_summary = "\n".join(
            [
                f"- {v['severity'].upper()}: {v['rule_id']} in {v['file_path']}:{v['start_line']}"
                for v in violations[:20]  # Limit to top 20
            ]
        )

        messages = [
            {"role": "system", "content": SCAN_SUMMARY_PROMPT["system"]},
            {
                "role": "user",
                "content": SCAN_SUMMARY_PROMPT["user"].format(
                    total_violations=len(violations),
                    critical_count=sum(1 for v in violations if v["severity"] == "critical"),
                    high_count=sum(1 for v in violations if v["severity"] == "high"),
                    medium_count=sum(1 for v in violations if v["severity"] == "medium"),
                    low_count=sum(1 for v in violations if v["severity"] == "low"),
                    violation_summary=violation_summary,
                ),
            },
        ]

        return await self.generate(messages, temperature=0.3, max_tokens=500)


# Global service instance
llm_service = LLMService()