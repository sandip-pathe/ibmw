"""
Multi-Agent Compliance System using LangGraph.
"""
import json
from typing import Annotated, TypedDict, List, Literal
from uuid import UUID

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from loguru import logger

from app.config import get_settings
from app.services.tools import COMPLIANCE_TOOLS
from app.services.agents import AgentLogger

settings = get_settings()

# --- State Definition ---
class ComplianceState(TypedDict):
    repo_id: str
    rule_id: str
    rule_text: str
    scan_id: str
    
    # Agent Memory
    messages: List[BaseMessage]
    plan: str
    relevant_files: List[str]
    violation_report: dict | None

# --- Nodes ---

async def planner_node(state: ComplianceState):
    """Agent 1: Legal Mind. Analyzes the rule and creates a search strategy."""
    scan_id = state["scan_id"]
    agent_logger = AgentLogger(scan_id)
    await agent_logger.log("PLANNER", f"Analyzing intent for rule: {state['rule_id']}")
    
    llm = ChatOpenAI(
        api_key=settings.openai_api_key or "dummy", # Fallback if using Azure adapter
        model="gpt-4o", 
        temperature=0
    )
    
    # In production use Azure adapter if configured
    
    messages = [
        HumanMessage(content=f"""
        You are a Compliance Planning Agent.
        Rule: "{state['rule_text']}"
        
        Identify the technical keywords, file types, and logic patterns I need to look for in a codebase to validate this rule.
        Output a concise search strategy.
        """)
    ]
    
    response = await llm.ainvoke(messages)
    plan = response.content
    
    await agent_logger.log("PLANNER", f"Strategy devised: {plan[:100]}...")
    
    return {"plan": plan, "messages": [response]}

async def navigator_node(state: ComplianceState):
    """Agent 2: Scout. Uses tools to find code."""
    scan_id = state["scan_id"]
    agent_logger = AgentLogger(scan_id)
    await agent_logger.log("NAVIGATOR", "Executing search strategy...")
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(COMPLIANCE_TOOLS)
    
    # Context for the scout
    messages = state["messages"] + [
        HumanMessage(content=f"""
        Based on the plan: "{state['plan']}"
        Use the search_codebase tool to find relevant code in repo {state['repo_id']}.
        Search for specific keywords mentioned in the plan.
        """)
    ]
    
    # This simple node invokes the LLM which might decide to call a tool
    response = await llm.ainvoke(messages)
    
    return {"messages": [response]}

async def investigator_node(state: ComplianceState):
    """Agent 3: Engineer. Analyzes the found code for violations."""
    scan_id = state["scan_id"]
    agent_logger = AgentLogger(scan_id)
    
    # Extract tool outputs from history (simplified)
    # In real LangGraph, we'd parse ToolMessages
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if we actually have code content in the context
    # If the previous node called a tool, the tool output is in the state history
    
    await agent_logger.log("INVESTIGATOR", "Analyzing retrieved code context...")
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    analysis_prompt = f"""
    You are a Compliance Investigator.
    Rule: "{state['rule_text']}"
    
    Review the search results and conversation history above.
    1. Does the code violate the rule?
    2. If yes, provide specific file paths, line numbers, and reasoning.
    3. Rate severity (critical, high, medium, low).
    
    Return JSON format ONLY:
    {{
        "verdict": "compliant" | "non_compliant",
        "explanation": "...",
        "severity": "...",
        "file_path": "..."
    }}
    
    If no relevant code was found or inconclusive, return verdict "unknown".
    """
    
    response = await llm.ainvoke(messages + [HumanMessage(content=analysis_prompt)])
    
    content = response.content
    # Clean markdown json
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        
    try:
        report = json.loads(content)
        await agent_logger.log("INVESTIGATOR", f"Verdict: {report.get('verdict', 'unknown')}")
    except:
        report = {"verdict": "unknown", "explanation": "Failed to parse analysis"}
        
    return {"violation_report": report}

# --- Edges ---

def should_continue_search(state: ComplianceState) -> Literal["tools", "investigator"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM wants to call a tool, go to tool node
    if last_message.tool_calls:
        return "tools"
    # Otherwise go to investigation
    return "investigator"

# --- Graph Construction ---

def build_compliance_graph():
    workflow = StateGraph(ComplianceState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("navigator", navigator_node)
    workflow.add_node("tools", ToolNode(COMPLIANCE_TOOLS))
    workflow.add_node("investigator", investigator_node)
    
    workflow.set_entry_point("planner")
    
    workflow.add_edge("planner", "navigator")
    
    workflow.add_conditional_edges(
        "navigator",
        should_continue_search,
    )
    
    workflow.add_edge("tools", "navigator") # Loop back to navigator to process tool output or search more
    workflow.add_edge("investigator", END)
    
    return workflow.compile()

# Singleton graph
compliance_graph = build_compliance_graph()

async def run_agentic_analysis(scan_id: str, repo_id: str, rule_id: str, rule_text: str):
    """Entry point to run the graph for a single rule."""
    initial_state = {
        "repo_id": repo_id,
        "rule_id": rule_id,
        "rule_text": rule_text,
        "scan_id": scan_id,
        "messages": [],
        "plan": "",
        "relevant_files": [],
        "violation_report": None
    }
    
    result = await compliance_graph.ainvoke(initial_state)
    return result["violation_report"]