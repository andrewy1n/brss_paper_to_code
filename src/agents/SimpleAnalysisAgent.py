from openai import OpenAI
import os
import json
from .BaseAgent import BaseAgent

class SimpleAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def call(self, prompt: str) -> str:
        try:
            messages = [{
                "role": "system",
                "content": """You are a Python code analysis expert. Your role is to analyze code and provide high-level recommendations for improvement.
                    Focus on:
                    1. Code organization and structure
                    2. Design patterns and architectural decisions
                    3. Potential bugs or issues
                    4. Performance considerations
                    5. Best practices and coding standards
                    6. Documentation needs
                    7. Testing requirements

                Provide your analysis in a clear, structured format with specific recommendations and make sure to include specific file names and line numbers."""
            }]
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=10000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return json.dumps({"error": str(e)})
