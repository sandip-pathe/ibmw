from pydantic import BaseModel
import re

class Rule(BaseModel):
    condition: str = ""
    actor: str = ""
    object: str = ""
    action: str = ""
    outcome: str = ""
    raw_text: str = ""
    keywords: list = []

def normalize_rule_text(rule_text: str) -> Rule:
    """
    Heuristic + LLM fallback for rule normalization.
    """
    # Heuristic extraction
    actor = ""
    action = ""
    obj = ""
    condition = ""
    outcome = ""
    keywords = re.findall(r'\b\w+\b', rule_text)
    # Simple heuristics
    if "if" in rule_text.lower():
        condition = rule_text.split("if", 1)[-1].strip()
    if "must" in rule_text.lower():
        action = "must"
    # LLM fallback (pseudo-code, replace with actual call)
    # llm_result = llm.complete(f"Extract actor, action, object, condition, outcome from: {rule_text}")
    # Parse llm_result...
    return Rule(
        condition=condition,
        actor=actor,
        object=obj,
        action=action,
        outcome=outcome,
        raw_text=rule_text,
        keywords=keywords,
    )
