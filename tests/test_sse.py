import requests
import json
import sys
from pathlib import Path

def test_generate(file_id: str):
    response = requests.get(
        f"http://localhost:8000/generate/{file_id}",
        stream=True,
        headers={"Accept": "text/event-stream"}
    )
    
    # Process the SSE stream
    for line in response.iter_lines():
        if line:
            # Remove the "data: " prefix and parse JSON
            data = json.loads(line.decode('utf-8').replace('data: ', ''))
            print(data)
            
            # If we have files in the response, print them
            if 'files' in data:
                print("\nGenerated files:")
                for file in data['files']:
                    print(f"- {file}")
            
            # If we get an error or completion, break
            if data['status'] in ['error', 'complete']:
                break

def main():
    test_generate("1ffc7431-b925-4052-b83c-9eb479118a9f")

if __name__ == "__main__":
    main() 