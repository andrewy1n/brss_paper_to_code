import os
import asyncio
from fastapi import UploadFile
import httpx
from pathlib import Path

async def test_upload_paper():
    print("\nTesting paper upload functionality...")
    
    # Get the path to the example paper
    paper_path = Path("brss_paper_to_code/paper_examples/101411H.pdf")
    if not paper_path.exists():
        print(f"❌ Test failed: Example paper not found at {paper_path}")
        return
    
    print(f"Found example paper at {paper_path}")
    
    try:
        # Create an async client
        async with httpx.AsyncClient() as client:
            # Test file upload
            print("Uploading paper via file upload...")
            with open(paper_path, 'rb') as f:
                file = UploadFile(
                    file_name="101411H.pdf",
                    file=f
                )
                response = await client.post(
                    "http://localhost:8000/upload",
                    files={"file": file}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Upload successful! File ID: {result['file_id']}")
                    return result['file_id']
                else:
                    print(f"❌ Upload failed with status {response.status_code}")
                    print(f"Error: {response.text}")
                    return None
                    
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return None

async def test_upload_with_url():
    print("\nTesting paper upload with URL...")
    
    # Example URL (replace with actual URL if needed)
    pdf_url = "https://example.com/sample.pdf"
    
    try:
        async with httpx.AsyncClient() as client:
            print("Uploading paper via URL...")
            response = await client.post(
                "http://localhost:8000/upload",
                data={"pdf_url": pdf_url}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ URL upload successful! File ID: {result['file_id']}")
                return result['file_id']
            else:
                print(f"❌ URL upload failed with status {response.status_code}")
                print(f"Error: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return None

async def test_generate_code(file_id: str):
    if not file_id:
        print("❌ Cannot test code generation without a valid file ID")
        return
        
    print(f"\nTesting code generation for file ID: {file_id}")
    
    try:
        async with httpx.AsyncClient() as client:
            print("Starting code generation...")
            response = await client.get(
                f"http://localhost:8000/generate/{file_id}",
                headers={"Accept": "text/event-stream"}
            )
            
            if response.status_code == 200:
                print("✅ Code generation started successfully")
                # Process the SSE stream
                for line in response.iter_lines():
                    if line:
                        print(f"Event: {line.decode('utf-8')}")
            else:
                print(f"❌ Code generation failed with status {response.status_code}")
                print(f"Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")

async def main():
    print("Starting upload tests...")
    
    # Test file upload
    file_id = await test_upload_paper()
    if file_id:
        # Test code generation with the uploaded file
        await test_generate_code(file_id)
    
    # Test URL upload (commented out as it requires a valid URL)
    # await test_upload_with_url()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
