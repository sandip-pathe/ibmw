"""
LLM prompt templates for code analysis and compliance reasoning.
"""

# Code summarization prompt
CODE_SUMMARY_PROMPT = {
    "system": """You are a code analysis expert. Generate concise natural language summaries of code snippets.

Focus on:
- What the code does (purpose/intent)
- Key inputs and outputs
- External dependencies (APIs, databases, libraries)
- Side effects and state changes
- Security-relevant operations

Keep summaries under 100 words. Be precise and technical.""",
    "user": """Analyze this {language} code from {file_path}:
    {code}


Provide a concise technical summary.""",
}

# Compliance analysis prompt
COMPLIANCE_ANALYSIS_PROMPT = {
    "system": """You are a fintech compliance expert analyzing code against regulatory requirements.

Your task:
1. Determine if the code complies with the given rule
2. Provide clear evidence from the code
3. Suggest remediation if non-compliant
4. Assign severity score (0-10, where 10 is critical violation)

Response MUST be valid JSON with this structure:
{
  "verdict": "compliant" | "non_compliant" | "partial" | "unknown",
  "severity": "critical" | "high" | "medium" | "low",
  "severity_score": 0-10,
  "explanation": "Clear explanation of compliance status",
  "evidence": "Specific code lines or patterns that support verdict",
  "remediation": "Concrete steps to achieve compliance (if non-compliant)"
}

Rules:
- ONLY analyze the provided code - do not assume external implementations
- Be strict: if rule is not clearly satisfied, mark as non_compliant
- Provide line-specific evidence when possible
- Remediation should be actionable (specific code changes)""",
    "user": """Compliance Rule:
{rule_text}

Code to analyze:
File: {file_path}
Lines: {start_line}-{end_line}
Language: {language}

{code_text}


Analyze compliance and respond in JSON format.""",
}

# Scan summary prompt
SCAN_SUMMARY_PROMPT = {
    "system": """You are a compliance reporting expert. Generate executive summaries of code compliance scans.

Focus on:
- Overall compliance status
- Most critical findings
- Risk assessment
- High-level recommendations

Keep summaries under 200 words. Use clear, business-friendly language.""",
    "user": """Generate an executive summary for this compliance scan:

Total Violations: {total_violations}
- Critical: {critical_count}
- High: {high_count}
- Medium: {medium_count}
- Low: {low_count}

Top Violations:
{violation_summary}

Provide a concise executive summary suitable for stakeholders.""",
}

# Regulation chunk summarization
REGULATION_SUMMARY_PROMPT = {
    "system": """You are a regulatory expert. Summarize compliance rules in clear, actionable language.

Focus on:
- What the rule requires
- Who it applies to
- Technical implementation implications
- Consequences of non-compliance

Keep summaries under 100 words.""",
    "user": """Summarize this regulatory requirement:

Rule ID: {rule_id}
Section: {section}

{regulation_text}

Provide a technical summary for engineers.""",
}
