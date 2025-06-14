from openai import OpenAI
import os
import ast
import json
from typing import Dict, List, Any
from .BaseAgent import BaseAgent

tools = [{
    "name": "ast_analysis",
    "description": "Analyze Python code structure using AST to get detailed information about imports, classes, functions, and variables",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python source code to analyze"
            }
        },
        "required": ["code"]
    }
}]

class CodeAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def ast_analysis(self, code: str) -> Dict[str, Any]:
        """Analyze Python code structure using AST."""
        try:
            tree = ast.parse(code)
            
            analysis = {
                "code_structure": {
                    "imports": [],
                    "classes": [],
                    "functions": [],
                    "variables": []
                }
            }
            
            # Analyze imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        analysis["code_structure"]["imports"].append({
                            "name": name.name,
                            "type": "import",
                            "line": node.lineno
                        })
                elif isinstance(node, ast.ImportFrom):
                    for name in node.names:
                        analysis["code_structure"]["imports"].append({
                            "name": f"{node.module}.{name.name}",
                            "type": "from import",
                            "line": node.lineno
                        })
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [],
                        "attributes": []
                    }
                    
                    # Get methods and attributes
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_info["methods"].append(item.name)
                        elif isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    class_info["attributes"].append(target.id)
                    
                    analysis["code_structure"]["classes"].append(class_info)
                
                elif isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "params": [arg.arg for arg in node.args.args],
                        "returns": "None"  # Default return type
                    }
                    
                    # Try to determine return type
                    for item in ast.walk(node):
                        if isinstance(item, ast.Return) and item.value:
                            if isinstance(item.value, ast.Name):
                                func_info["returns"] = item.value.id
                            elif isinstance(item.value, ast.Constant):
                                func_info["returns"] = type(item.value.value).__name__
                    
                    analysis["code_structure"]["functions"].append(func_info)
                
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_info = {
                                "name": target.id,
                                "line": node.lineno,
                                "type": "unknown"  # Default type
                            }
                            
                            # Try to determine variable type
                            if isinstance(node.value, ast.Constant):
                                var_info["type"] = type(node.value.value).__name__
                            elif isinstance(node.value, ast.Call):
                                var_info["type"] = "function_call"
                            
                            analysis["code_structure"]["variables"].append(var_info)
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    def call(self, file_path: str) -> str:
        try:
            # Read the file
            with open(file_path, "r") as file:
                code = file.read()
            
            # Get additional insights using OpenAI
            messages = [{
                "role": "system",
                "content": """You are a Python code analysis expert. Your role is to analyze code structure and provide detailed insights and recommendations.
You have access to AST analysis through the ast_analysis function, which can provide detailed information about the code structure.
Use this information to provide comprehensive analysis and recommendations."""
            }]
            
            messages.append({
                "role": "user",
                "content": f"Analyze the following Python code and provide insights:\n{code}"
            })
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "ast_analysis"}},
                max_tokens=10000
            )
            
            response_message = response.choices[0].message
            
            # If the model wants to use AST analysis
            if response_message.tool_calls:
                tool_call = response_message.tool_calls[0]
                if tool_call.function.name == "ast_analysis":
                    # Get AST analysis
                    ast_results = self.ast_analysis(code)
                    
                    # Add the model's analysis
                    ast_results["analysis"] = {
                        "structure_analysis": response_message.content or "",
                        "improvements": "",
                        "dependencies": "",
                        "code_quality": "",
                        "best_practices": ""
                    }
                    
                    # Get additional insights based on AST results
                    follow_up_messages = messages + [
                        {"role": "assistant", "content": None, "tool_calls": [tool_call]},
                        {"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(ast_results)}
                    ]
                    
                    follow_up_response = self.client.chat.completions.create(
                        model="gpt-4",
                        messages=follow_up_messages,
                        max_tokens=1000
                    )
                    
                    # Update analysis with the model's insights
                    ast_results["analysis"]["structure_analysis"] = follow_up_response.choices[0].message.content
                    
                    return json.dumps(ast_results)
            
            # If no tool calls, return basic analysis
            return json.dumps({
                "analysis": {
                    "structure_analysis": response_message.content,
                    "improvements": "",
                    "dependencies": "",
                    "code_quality": "",
                    "best_practices": ""
                }
            })
            
        except Exception as e:
            return json.dumps({"error": str(e)})