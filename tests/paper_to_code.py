import re
import subprocess
import sys
from pathlib import Path
from PyPDF2 import PdfReader
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com")

OUTPUT_DIR = "generated_project"


def validate_module_name(module: str) -> bool:
    """Ensure module name is safe for installation"""
    return re.match(r'^[a-zA-Z0-9_-]+$', module) is not None


def install_module(module: str) -> bool:
    if not validate_module_name(module):
        print(f"Invalid module name: {module}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", module],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True)
        print(f"Successfully installed {module}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Installation failed for {module}: {e.stderr}")
        return False
    except Exception as e:
        print(f"Error installing {module}: {str(e)}")
        return False


def read_pdf(pdf_path: str) -> str:
    try:
        reader = PdfReader(pdf_path)
        text = " ".join([page.extract_text() for page in reader.pages])
        return text
    except Exception as e:
        raise RuntimeError(f"PDF reading failed: {str(e)}")


def llm_query(prompt: str, retries=3) -> str:
    print("\nSending prompt to LLM...")

    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {
                "role":
                "system",
                "content":
                "You are an expert in geospatial algorithmic coding in Python."
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        stream=False)

    message_content = response.choices[0].message.content

    if not message_content:
        print("Something went wrong, no LLM content!")
        return ""

    return message_content

def extract_all_code_blocks(response: str) -> dict:
    matches = re.findall(r'```([\w./\\-]+)\n(.*?)```', response, re.DOTALL)
    if not matches:
        raise ValueError("No code blocks with filenames found in LLM response")

    return {filename.strip(): code.strip() for filename, code in matches}


def execute_code(code: str,
                 attempt: int,
                 filename: str = "temp_code.py",
                 working_dir: str = ".") -> dict:
    result = {"success": False, "error": "", "missing_module": None}

    try:
        process = subprocess.run(
            [sys.executable, filename],
            capture_output=True,
            text=True,
            timeout=300,
            check=True,
            cwd=working_dir)  # <== run inside output folder
        result["success"] = True
    except subprocess.CalledProcessError as e:
        error_msg = f"Error {e.returncode}:\n{e.stderr}"
        result["error"] = error_msg
        # Detect missing modules
        missing_module = re.search(r"No module named '([^']+)'", e.stderr)
        if missing_module:
            result["missing_module"] = missing_module.group(1)
    except subprocess.TimeoutExpired:
        result["error"] = "Execution timed out (300 seconds)"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
    finally:
        if Path(filename).exists():
            Path(filename).unlink()

    return result


def self_heal_loop(initial_prompt: str, max_attempts=5) -> dict:
    current_prompt = initial_prompt
    error_history = []

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n--- Attempt {attempt}/{max_attempts} ---")

        response = llm_query(current_prompt)
        try:
            file_map = extract_all_code_blocks(response)
            print("Extracted files:\n", list(file_map.keys()))
        except ValueError as e:
            error_msg = f"Code extraction failed: {str(e)}"
            print(error_msg)
            error_history.append(error_msg)
            current_prompt = f"{initial_prompt}\n\nPrevious error: {error_msg}"
            continue

        for filename, code in file_map.items():
            file_path = os.path.join(OUTPUT_DIR, filename)
            os.makedirs(os.path.dirname(file_path),
                        exist_ok=True)  # In case of subfolders
            with open(file_path, "w") as f:
                f.write(code)
            print(f"Saved: {file_path}")

        # Run entry file (e.g., main.py or implemented_app.py)
        entry = "main.py" if "main.py" in file_map else "implemented_app.py"
        execution_result = execute_code(file_map.get(entry, ""),
                                        attempt,
                                        filename=entry,
                                        working_dir=OUTPUT_DIR)

        install_attempts = 0
        max_install_tries = 3

        while (not execution_result["success"]
               and execution_result.get("missing_module")
               and install_attempts < max_install_tries):
            module = execution_result["missing_module"]
            print(f"Missing package detected: {module}. Installing...")

            if install_module(module):
                print("Re-running code after installation...")
                execution_result = execute_code(file_map.get(entry, ""),
                                                attempt,
                                                filename=entry,
                                                working_dir=OUTPUT_DIR)
                install_attempts += 1
            else:
                error_msg = f"Failed to install {module}"
                error_history.append(error_msg)
                break

        if execution_result["success"]:
            return file_map

        print(f"{execution_result['error']} \n")

        error_history.append(execution_result["error"])
        current_prompt = (
            f"Original task: {initial_prompt}\n\n"
            f"Previous code:\n```python\n{file_map}\n```\n\n"
            f"Last error:\n{execution_result['error']}\n\n"
            f"Error history:\n{chr(10).join(error_history[-3:])}\n\n"
            "Please fix this code considering the dependency issues.")

    raise RuntimeError(f"Failed to resolve after {max_attempts} attempts")


def main(pdf_path: str):
    """Main processing pipeline"""
    try:
        # 1. Read PDF
        print(f"Reading PDF: {pdf_path}")
        paper_text = read_pdf(pdf_path)

        print(f"PDF Length: {len(paper_text)}")

        # 2. Create initial prompt
        initial_prompt = (
            "Convert this research paper into working Python code. "
            "Focus on implementing core algorithms and concepts.\n\n"
            "Break down the implementation into multiple files if appropriate"
            f"Paper content:\n{paper_text}..."
            "The application will be executed using the command: 'python main.py'.\n"
            "Return code blocks in the following format:\n"
            "```filename.py\n<code here>\n```\n"
            "Wrap each file’s code in a code block like this. Do NOT add explanation or comments outside code blocks.\n\n"
        )

        # 3. Start self-healing process
        final_files = self_heal_loop(initial_prompt)

        # 4. Save final code
        for filename, code in final_files.items():
            with open(filename, "w") as f:
                f.write(code)
            print(f"Saved: {filename}")

    except Exception as e:
        print(f"Critical error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python paper_to_code.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    main(pdf_path)
