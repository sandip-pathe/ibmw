class FlowGraph:
    def __init__(self):
        self.nodes = set()
        self.edges = []  # (caller, callee)
        self.imports = set()

    def add_node(self, name):
        self.nodes.add(name)

    def add_edge(self, caller, callee):
        self.edges.append((caller, callee))

    def add_import(self, imp):
        self.imports.add(imp)

    def to_dict(self):
        return {
            "nodes": list(self.nodes),
            "edges": self.edges,
            "imports": list(self.imports),
        }
def build_flow_graph(repo_id: str, repo_path: str) -> FlowGraph:
    """
    Build a lightweight flow graph for a repo.
    Detects imports and function calls inside functions.
    """
    graph = FlowGraph()
    import ast
    import os
    for root, _, files in os.walk(repo_path):
        for fname in files:
            if fname.endswith(".py"):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        code = f.read()
                    tree = ast.parse(code)
                    # Imports
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for n in node.names:
                                graph.add_import(n.name)
                        elif isinstance(node, ast.ImportFrom):
                            graph.add_import(node.module)
                    # Functions and calls
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            graph.add_node(node.name)
                            for subnode in ast.walk(node):
                                if isinstance(subnode, ast.Call):
                                    if hasattr(subnode.func, "id"):
                                        graph.add_edge(node.name, subnode.func.id)
                                    elif hasattr(subnode.func, "attr"):
                                        graph.add_edge(node.name, subnode.func.attr)
                except Exception:
                    continue
    return graph
import ast
import json
import yaml
import os
import re
def extract_constants_from_code(code: str) -> dict:
    """Extracts constant assignments from Python code."""
    constants = {}
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(node.value, (ast.Constant, ast.Num, ast.Str)):
                            constants[target.id] = getattr(node.value, 'value', node.value.n if hasattr(node.value, 'n') else None)
    except Exception:
        pass
    return constants
def extract_config_from_file(file_path: str) -> dict:
    """Extracts config from JSON, YAML, or .env files."""
    ext = os.path.splitext(file_path)[-1].lower()
    try:
        with open(file_path, 'r') as f:
            if ext == '.json':
                return json.load(f)
            elif ext in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif ext == '.env':
                return dict(line.split('=', 1) for line in f if '=' in line)
    except Exception:
        return {}
    return {}
def detect_function_calls(code: str) -> dict:
    """Detects function calls inside functions for simple control-flow."""
    calls = {}
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                calls[node.name] = []
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call) and hasattr(subnode.func, 'id'):
                        calls[node.name].append(subnode.func.id)
    except Exception:
        pass
    return calls
def find_hardcoded_thresholds(constants: dict) -> dict:
    """Detects hardcoded thresholds (e.g., limits, max, min)."""
    thresholds = {}
    for k, v in constants.items():
        if re.search(r'(limit|max|min|threshold)', k, re.I):
            thresholds[k] = v
    return thresholds
def detect_overrides_across_files(functions: dict, all_files: dict) -> dict:
    """Detects overrides of constants/functions across files."""
    overrides = {}
    for fname, fdict in all_files.items():
        for func, calls in fdict.get('calls', {}).items():
            for call in calls:
                if call in functions:
                    overrides.setdefault(call, []).append(fname)
    return overrides
def detect_missing_error_handling(code: str) -> bool:
    """Detects if error handling (try/except) is missing in code."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                return False
        return True
    except Exception:
        return True
"""
Code parsing service using Tree-sitter for AST analysis.
"""
import re
from pathlib import Path
from typing import Optional

from loguru import logger
from tree_sitter import Language, Parser

from app.config import get_settings
from app.core.exceptions import CodeParsingError

settings = get_settings()


class CodeParser:
    """
    Tree-sitter based code parser supporting multiple languages.
    
    NOTE: Tree-sitter language bindings need to be built separately.
    For hackathon demo, this provides the interface with fallback.
    """

    def __init__(self):
        self.parsers: dict[str, Parser] = {}
        self.languages_available = ["python", "javascript", "typescript", "java"]

        # Initialize parsers (stub for demo - in production, load compiled languages)
        self._init_parsers()

    def _init_parsers(self) -> None:
        """Initialize Tree-sitter parsers (stubbed for demo)."""
        # In production, you would build and load language libraries:
        # Language.build_library(
        #     'build/languages.so',
        #     ['vendor/tree-sitter-python', 'vendor/tree-sitter-javascript', ...]
        # )
        # Then load: Language('build/languages.so', 'python')

        logger.warning(
            "Tree-sitter parsers not fully initialized - using fallback text parsing"
        )
        # For demo, we'll use regex-based fallback

    def get_language_from_extension(self, file_path: str) -> Optional[str]:
        """
        Detect programming language from file extension.

        Args:
            file_path: File path

        Returns:
            Language identifier or None
        """
        ext = Path(file_path).suffix.lower()
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".c": "c",
            ".h": "c",
        }
        return mapping.get(ext)

    def parse_file(self, file_path: str, content: str) -> Optional[dict]:
        """
        Parse file and return AST (stubbed for demo).

        Args:
            file_path: File path
            content: File content

        Returns:
            AST representation or None if parsing fails
        """
        language = self.get_language_from_extension(file_path)
        if not language:
            return None

        # In production, use Tree-sitter parser
        # parser = self.parsers.get(language)
        # tree = parser.parse(bytes(content, "utf8"))
        # return tree.root_node

        # For demo, return placeholder
        return {"language": language, "type": "module", "content": content}


    def extract_functions_fallback(
        self, content: str, language: str
    ) -> list[dict[str, any]]:
        """
        Fallback function extraction using regex (for demo without full Tree-sitter).
        Populates code_map fields: call_links, semantic_tags, variables, config_keys.
        """
        chunks = []
        semantic_tags = []
        # Simple tag detection (demo)
        tag_keywords = ["kyc", "storage", "upi", "auth", "payment", "compliance"]
        for tag in tag_keywords:
            if tag in content.lower():
                semantic_tags.append(tag)

        if language == "python":
            pattern = r"^(class|def|async def)\s+(\w+)"
            lines = content.split("\n")
            for i, line in enumerate(lines):
                match = re.match(pattern, line.strip())
                if match:
                    node_type = match.group(1)
                    name = match.group(2)
                    start_line = i + 1
                    end_line = start_line
                    base_indent = len(line) - len(line.lstrip())
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() and not lines[j].strip().startswith("#"):
                            current_indent = len(lines[j]) - len(lines[j].lstrip())
                            if current_indent <= base_indent:
                                end_line = j
                                break
                    else:
                        end_line = len(lines)
                    chunk_text = "\n".join(lines[i:end_line])
                    # Extract call_links
                    call_links = list(set([call for call_list in detect_function_calls(chunk_text).values() for call in call_list]))
                    # Extract variables
                    variables = extract_constants_from_code(chunk_text)
                    # Extract config_keys
                    config_keys = find_hardcoded_thresholds(variables)
                    chunks.append(
                        {
                            "type": "function" if "def" in node_type else "class",
                            "name": name,
                            "start_line": start_line,
                            "end_line": end_line,
                            "text": chunk_text,
                            "call_links": call_links,
                            "variables": variables,
                            "config_keys": config_keys,
                            "semantic_tags": semantic_tags,
                        }
                    )
        elif language in ["javascript", "typescript"]:
            pattern = r"^(function|class|const|let|var)\s+(\w+)"
            lines = content.split("\n")
            for i, line in enumerate(lines):
                match = re.match(pattern, line.strip())
                if match:
                    node_type = match.group(1)
                    name = match.group(2)
                    start_line = i + 1
                    brace_count = line.count("{") - line.count("}")
                    end_line = start_line
                    for j in range(i + 1, len(lines)):
                        brace_count += lines[j].count("{") - lines[j].count("}")
                        if brace_count <= 0:
                            end_line = j + 1
                            break
                    else:
                        end_line = len(lines)
                    chunk_text = "\n".join(lines[i:end_line])
                    # JS/TS: call_links, variables, config_keys, semantic_tags (stub)
                    call_links = []
                    variables = {}
                    config_keys = {}
                    chunks.append(
                        {
                            "type": "function" if node_type == "function" else "declaration",
                            "name": name,
                            "start_line": start_line,
                            "end_line": end_line,
                            "text": chunk_text,
                            "call_links": call_links,
                            "variables": variables,
                            "config_keys": config_keys,
                            "semantic_tags": semantic_tags,
                        }
                    )
        return chunks
    
    def parse_file_changes(
        self,
        file_path: str,
        old_content: Optional[str],
        new_content: str
    ) -> dict[str, any]:
        """
        Parse file changes for incremental updates (webhook support).
        
        Args:
            file_path: File path
            old_content: Previous file content (None if new file)
            new_content: Current file content
            
        Returns:
            Change information including delta_type
        """
        language = self.get_language_from_extension(file_path)
        if not language:
            return {"delta_type": "unknown", "chunks": []}
        
        # Parse new content
        new_chunks = self.extract_functions_fallback(new_content, language)
        
        # Determine delta type
        if old_content is None:
            delta_type = "added"
            for chunk in new_chunks:
                chunk["delta_type"] = "added"
                chunk["previous_hash"] = None
        elif old_content == new_content:
            delta_type = "unchanged"
            for chunk in new_chunks:
                chunk["delta_type"] = "unchanged"
        else:
            delta_type = "modified"
            # Parse old content for comparison
            old_chunks = self.extract_functions_fallback(old_content, language)
            old_chunk_map = {c["name"]: c for c in old_chunks}
            
            for chunk in new_chunks:
                old_chunk = old_chunk_map.get(chunk["name"])
                if old_chunk:
                    if old_chunk["text"] == chunk["text"]:
                        chunk["delta_type"] = "unchanged"
                    else:
                        chunk["delta_type"] = "modified"
                        chunk["previous_hash"] = self._hash_text(old_chunk["text"])
                else:
                    chunk["delta_type"] = "added"
                    chunk["previous_hash"] = None
        
        return {
            "delta_type": delta_type,
            "chunks": new_chunks,
            "language": language
        }
    
    def _hash_text(self, text: str) -> str:
        """Hash text content for change detection"""
        import hashlib
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Global parser instance
code_parser = CodeParser()