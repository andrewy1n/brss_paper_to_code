import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).parent.parent))
from src.agents.CodeAnalysisAgent import CodeAnalysisAgent

def format_analysis(analysis: dict) -> None:
    print("\n=== Code Analysis Results ===\n")
    
    code_structure = analysis.get('code_structure', {})
    insights = analysis.get('analysis', {})
    
    # Print code structure
    if 'imports' in code_structure:
        print("📦 Imports:")
        for imp in code_structure['imports']:
            print(f"  - {imp['name']} ({imp['type']}) at line {imp['line']}")
        print()
    
    if 'classes' in code_structure:
        print("🏗️  Classes:")
        for cls in code_structure['classes']:
            print(f"  - {cls['name']} at line {cls['line']}")
            if 'methods' in cls:
                print(f"    Methods: {', '.join(cls['methods'])}")
            if 'attributes' in cls:
                print(f"    Attributes: {', '.join(cls['attributes'])}")
        print()
    
    if 'functions' in code_structure:
        print("⚡ Functions:")
        for func in code_structure['functions']:
            print(f"  - {func['name']} at line {func['line']}")
            if 'params' in func:
                print(f"    Parameters: {', '.join(func['params'])}")
            if 'returns' in func:
                print(f"    Returns: {func['returns']}")
        print()
    
    if 'variables' in code_structure:
        print("📝 Variables:")
        for var in code_structure['variables']:
            print(f"  - {var['name']} ({var['type']}) at line {var['line']}")
        print()
    
    # Print analysis insights
    print("🔍 Analysis Insights:")
    for key, value in insights.items():
        if value:  # Only print if there's content
            print(f"\n{key.replace('_', ' ').title()}:")
            print(f"  {value}")
    print()

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_code_analysis_agent.py <path_to_python_file>")
        sys.exit(1)

    python_file = sys.argv[1]
    if not python_file.endswith('.py'):
        print("Error: Input file must be a Python file")
        sys.exit(1)

    try:
        # Initialize the agent
        agent = CodeAnalysisAgent()
        
        # Analyze the file
        print(f"Analyzing {python_file}...")
        analysis = agent.call(python_file)
        
        # Parse the JSON response
        analysis_dict = json.loads(analysis)
        
        # Format and display results
        format_analysis(analysis_dict)
        
        # Save raw analysis to JSON file
        output_file = f"{python_file}_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_dict, f, indent=2)
        print(f"\nRaw analysis saved to: {output_file}")

    except Exception as e:
        print(f"Error analyzing file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 