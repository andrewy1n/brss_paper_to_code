from openai import OpenAI
import os
import re
from agents.BaseAgent import BaseAgent

class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

    def call(self, prompt: str) -> str:
        messages = []

        messages.append({
            "role": "system",
            "content": """You are an expert in geospatial algorithmic coding in Python.
                You will be given the paper content and the coding implementation plan.
                Generate all required files and directories as specified in the implementation plan.
                Focus on implementing core algorithms and concepts.
                
                For each file or directory, use one of these formats:
                1. For files with content:
                ```path/filename.py
                <code here>
                ```
                
                2. For empty directories:
                ```path/directory/
                ```
                
                3. For files that should exist but be empty:
                ```path/filename.py
                ```
                
                Wrap each file or directory in a code block like this. Do NOT add explanation or comments outside code blocks.
                Make sure to include all directories mentioned in the implementation plan, even if they're empty."""
        })
        
        for entry in self.history:
            messages.append({"role": "user", "content": entry["prompt"]})
            messages.append({"role": "assistant", "content": entry["response"]})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model="deepseek-reasoner",
            messages=messages,
        )
        response_content = response.choices[0].message.content
        
        print(response_content)

        self.history.append({
            "prompt": prompt,
            "response": response_content
        })
        
        return self.extract_all_code_blocks(response_content)
    
    
    def extract_all_code_blocks(self, response: str) -> dict:
        """Extract all code blocks from the response, including empty directories."""
        # Match code blocks with any file extension or directory
        matches = re.findall(r'```([\w./\\-]+/?)\n?(.*?)```', response, re.DOTALL)
        if not matches:
            raise ValueError("No code blocks with filenames found in LLM response")

        code_blocks = {}
        for path, content in matches:
            # Clean up the path and content
            clean_path = path.strip()
            clean_content = content.strip()
            
            # Handle empty directories (ending with /)
            if clean_path.endswith('/'):
                code_blocks[clean_path] = None  # None indicates an empty directory
            else:
                code_blocks[clean_path] = clean_content

        return code_blocks