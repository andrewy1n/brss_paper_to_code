import os
import sys
import time
import shutil
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from PyPDF2 import PdfReader

from agents.PlanningAgent import PlanningAgent
from agents.CodingAgent import CodingAgent
from agents.CodeAnalysisAgent import CodeAnalysisAgent
from agents.SimpleAnalysisAgent import SimpleAnalysisAgent
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = "generated_projects"

class ProjectGenerator:
    def __init__(self):
        self.planning_agent = PlanningAgent()
        self.coding_agent = CodingAgent()
        self.analysis_agent = CodeAnalysisAgent()
        self.simple_analysis_agent = SimpleAnalysisAgent()
        self.project_dir = None

    def create_project_directory(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = f"project_{timestamp}"
        project_path = Path(OUTPUT_DIR) / project_name
        project_path.mkdir(parents=True, exist_ok=True)
        return str(project_path)

    def cleanup(self) -> None:
        if self.project_dir and os.path.exists(self.project_dir):
            try:
                shutil.rmtree(self.project_dir)
                print(f"Cleaned up project directory: {self.project_dir}")
            except Exception as e:
                print(f"Warning: Failed to clean up project directory: {str(e)}")

    def extract_implementation_details(self, content: str) -> str:
        implementation_sections = [
            r'(?i)implementation.*?\n',
            r'(?i)methodology.*?\n',
            r'(?i)algorithm.*?\n',
            r'(?i)methods.*?\n',
            r'(?i)system design.*?\n',
            r'(?i)architecture.*?\n',
            r'(?i)experimental setup.*?\n'
        ]
        
        sections = []
        for pattern in implementation_sections:
            matches = re.finditer(pattern + r'(.*?)(?=\n\s*\n|\Z)', content, re.DOTALL)
            for match in matches:
                section = match.group(0).strip()
                if section and len(section) > 50:  # Filter out very short sections
                    sections.append(section)
        
        if not sections:
            print("Error: No implementation sections found in the paper.")
            print("The paper must contain at least one of these sections:")
            print("- Implementation")
            print("- Methodology")
            print("- Algorithm")
            print("- Methods")
            print("- System Design")
            print("- Architecture")
            print("- Experimental Setup")
            self.cleanup()
            sys.exit(1)
        
        unique_sections = list(dict.fromkeys(sections))
        return "\n\n".join(unique_sections)

    def read_paper(self, paper_path: str) -> str:
        try:
            # Check if file is a PDF
            if not paper_path.lower().endswith('.pdf'):
                print("Error: Input file must be a PDF")
                self.cleanup()
                sys.exit(1)

            # Read PDF file
            reader = PdfReader(paper_path)
            content = ""
            
            # Extract text from each page
            for page in reader.pages:
                content += page.extract_text() + "\n"
            
            print(f"Successfully read PDF with {len(reader.pages)} pages")
            
            # Extract implementation details
            implementation_content = self.extract_implementation_details(content)
            print(f"Extracted {len(implementation_content)} characters of implementation details")
            return implementation_content
            
        except Exception as e:
            print(f"Error reading PDF: {str(e)}")
            self.cleanup()
            sys.exit(1)

    def generate_plan(self, paper_content: str) -> str:
        try:
            print("Generating implementation plan...")
            return self.planning_agent.call(paper_content)
        except Exception as e:
            print(f"Error generating plan: {str(e)}")
            self.cleanup()
            sys.exit(1)

    def implement_code(self, paper_content: str, plan: str) -> Dict[str, str]:
        try:
            print("Generating code implementation...")
            prompt = f"""
                Paper content:
                {paper_content}
                Plan:
                {plan}
            """
            return self.coding_agent.call(prompt)
        except Exception as e:
            print(f"Error implementing code: {str(e)}")
            self.cleanup()
            sys.exit(1)
    
    def analyze_code(self, paper_content: str, plan: str, code_blocks: Dict[str, str]) -> Dict[str, str]:
        try:
            print("Analyzing code...")
            prompt = f"""
                Paper content:\n{paper_content}
                Plan:\n{plan}
                Code blocks:\n{code_blocks}
            """
            return self.simple_analysis_agent.call(prompt)
        except Exception as e:
            print(f"Error analyzing code: {str(e)}")
            self.cleanup()
            sys.exit(1)

    def improve_code(self, code_blocks: Dict[str, str], analysis: str) -> Dict[str, str]:
        try:
            print("Improving code based on analysis...")
            
            # Prepare improvement prompt
            prompt = f"""Based on the following code analysis, improve the implementation:
            
            Code Analysis:
            {analysis}
            
            Current Implementation:
            {code_blocks}
            
            Please provide improved versions of the code files that need modification.
            Return code blocks in the following format:
            ```filename.py
            <code here>
            ```
            Only include files that need improvement."""
            
            improved_blocks = self.coding_agent.call(prompt)
            
            # Merge improved blocks with original blocks
            final_blocks = code_blocks.copy()
            final_blocks.update(improved_blocks)
            
            return final_blocks
            
        except Exception as e:
            print(f"Error improving code: {str(e)}")
            return code_blocks

    def write_files(self, code_blocks: Dict[str, str]) -> List[str]:
        written_files = []
        try:
            for file_path, content in code_blocks.items():
                full_path = os.path.join(self.project_dir, file_path)
                
                # Create parent directories if they don't exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Handle empty directories (content is None)
                if content is None and file_path.endswith('/'):
                    os.makedirs(full_path, exist_ok=True)
                    written_files.append(full_path)
                    continue
                
                # Write file content
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                written_files.append(full_path)
            return written_files
        except Exception as e:
            print(f"Error writing files: {str(e)}")
            self.cleanup()
            sys.exit(1)

    def generate_project(self, paper_path: str) -> None:
        try:
            self.project_dir = self.create_project_directory()
            print(f"Created project directory: {self.project_dir}")

            paper_content = self.read_paper(paper_path)

            print(paper_content)
            
            plan = self.generate_plan(paper_content)
            plan_path = os.path.join(self.project_dir, "implementation_plan.md")
            with open(plan_path, 'w', encoding='utf-8') as f:
                f.write(plan)
            print(f"Implementation plan written to: {plan_path}")

            # Initial code implementation
            code_blocks = self.implement_code(paper_content, plan)
            written_files = self.write_files(code_blocks)
            print(f"Generated {len(written_files)} files")

            # Get high-level analysis
            print("Performing high-level code analysis...")
            simple_analysis = self.analyze_code(paper_content, plan, code_blocks)
            analysis_path = os.path.join(self.project_dir, "code_analysis.md")
            with open(analysis_path, 'w', encoding='utf-8') as f:
                f.write(simple_analysis)
            print(f"High-level analysis written to: {analysis_path}")

            # Improve code based on analysis
            print("Improving code based on analysis...")
            improved_blocks = self.improve_code(code_blocks, simple_analysis)
            improved_files = self.write_files(improved_blocks)
            print(f"Generated {len(improved_files)} improved files")

            print("\nProject generation completed successfully!")
            print(f"Project location: {self.project_dir}")
            print("\nGenerated files:")
            for file in improved_files:
                print(f"- {file}")

        except Exception as e:
            print(f"Error generating project: {str(e)}")
            self.cleanup()
            sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <path_to_research_paper.pdf>")
        sys.exit(1)

    paper_path = sys.argv[1]
    generator = ProjectGenerator()
    generator.generate_project(paper_path)

if __name__ == "__main__":
    main()
