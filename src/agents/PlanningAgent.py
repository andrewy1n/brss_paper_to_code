from openai import OpenAI
import os
from .BaseAgent import BaseAgent

class PlanningAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def call(self, paper_content: str) -> str:
        messages = []
        
        messages.append({
            "role": "system",
            "content": """You are a research paper implementation specialist. Your role is to convert research paper content into detailed, actionable coding steps.

                For each paper, provide a structured implementation plan that includes:

                1. Project Structure
                - List all required files and directories
                - Specify the purpose of each file
                - Define the main entry point

                2. Dependencies
                - Required Python packages and versions
                - External libraries and tools
                - Dataset requirements and sources

                3. Implementation Steps
                - Break down the paper's methodology into codeable steps
                - Specify which files each component should be implemented in
                - Include any mathematical formulas or algorithms that need to be implemented

                4. Data Processing
                - Dataset preparation steps
                - Data preprocessing requirements
                - Expected data formats and structures

                Format your response in clear markdown with appropriate headers and code blocks where needed.
                """
        })
        
        for entry in self.history:
            messages.append({"role": "user", "content": entry["prompt"]})
            messages.append({"role": "assistant", "content": entry["response"]})

        messages.append({"role": "user", "content": paper_content})
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        response_content = response.choices[0].message.content
        
        self.history.append({
            "prompt": paper_content,
            "response": response_content
        })
        
        return response_content
