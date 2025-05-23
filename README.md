# Paper to Code

A powerful tool that automatically converts academic papers into working code implementations. This project uses AI agents to analyze academic papers, generate implementation plans, and create working code based on the paper's methodology and implementation details.

## Features

- PDF paper parsing and text extraction
- Automatic implementation plan generation
- Code generation based on paper content
- Code analysis and improvement
- Project structure generation
- Support for various implementation sections (Methodology, Algorithm, System Design, etc.)

## Project Structure

```
.
├── src/                    # Source code
│   ├── main.py            # Main project generator
│   └── agents/            # AI agents for different tasks
├── tests/                 # Test files
├── paper_examples/        # Example papers for testing
└── generated_projects/    # Output directory for generated code
```

## Requirements

- Python 3.x
- PyPDF2
- dotenv
- Other dependencies (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd paper-to-code
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with the following API keys:
```bash
DEEPSEEK_API_KEY=your_deepseek_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

1. Place your academic paper (PDF format) in the `paper_examples` directory.

2. Run the main script:
```bash
python src/main.py [path-to-paper]
```

3. The generated code will be available in the `generated_projects` directory, organized in timestamped folders.

## How It Works

1. **Paper Analysis**: The system reads and extracts implementation details from the PDF paper.
2. **Planning**: An AI agent generates an implementation plan based on the paper's content.
3. **Code Generation**: Another AI agent creates the initial code implementation.
4. **Analysis & Improvement**: The code is analyzed and improved based on best practices.
5. **Project Generation**: The final code is organized into a proper project structure.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add appropriate license information]

## Acknowledgments

- Thanks to all contributors and the academic community for their valuable research papers. 