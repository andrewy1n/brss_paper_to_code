import os
import asyncio
import tempfile
import uuid
from db import get_project_download_url, store_project_info, upload_pdf, get_pdf_url, upload_project
from supabase.lib.client_options import ClientOptions

def test_project_dir():
    # Create a temporary directory with some test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_file_path = os.path.join(temp_dir, "test.txt")
        with open(test_file_path, "w") as f:
            f.write("Test content")
        
        yield temp_dir

async def test_upload_and_retrieve():
    print("\nTesting upload and retrieve functionality...")
    # Generate a UUID for the project ID
    project_id = str(uuid.uuid4())
    print(f"Generated project ID: {project_id}")
    
    try:
        # Create test project directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file_path = os.path.join(temp_dir, "test.txt")
            with open(test_file_path, "w") as f:
                f.write("Test content")
            
            print("Created test directory with sample file")
            
            # Test upload
            print("Uploading to Supabase storage...")
            try:
                download_url = await upload_project(project_id, temp_dir)
                print(f"Upload successful! Download URL: {download_url}")
            except Exception as e:
                print(f"❌ Upload failed with error: {str(e)}")
                print("Please check:")
                print("1. Your Supabase URL and key are correct")
                print("2. The storage bucket 'project-code' exists and is accessible")
                print("3. Your RLS policies allow uploads to this bucket")
                return
            
            # Store project info
            print("Storing project info in database...")
            try:
                project_info = await store_project_info(project_id, download_url)
                print("Project info stored successfully")
            except Exception as e:
                print(f"❌ Failed to store project info: {str(e)}")
                print("Please check:")
                print("1. The 'projects' table exists in your database")
                print("2. Your RLS policies allow inserts to this table")
                return
            
            # Test retrieval
            print("Retrieving project download URL...")
            retrieved_url = await get_project_download_url(project_id)
            print(f"Retrieved URL: {retrieved_url}")
            
            if retrieved_url == download_url:
                print("✅ Test passed: Retrieved URL matches uploaded URL")
            else:
                print("❌ Test failed: Retrieved URL does not match uploaded URL")
    except Exception as e:
        print(f"❌ Test failed with unexpected error: {str(e)}")

async def test_pdf_storage():
    print("\nTesting PDF storage functionality...")
    file_id = str(uuid.uuid4())
    print(f"Generated file ID: {file_id}")
    
    try:
        # Create a test PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4\nTest PDF content")
            temp_file_path = temp_file.name
        
        try:
            # Test PDF upload
            print("Uploading test PDF to Supabase storage...")
            try:
                url = await upload_pdf(file_id, temp_file_path)
                print(f"PDF upload successful! URL: {url}")
            except Exception as e:
                print(f"❌ PDF upload failed with error: {str(e)}")
                print("Please check:")
                print("1. Your Supabase URL and key are correct")
                print("2. The storage bucket 'pdf' exists and is accessible")
                print("3. Your RLS policies allow uploads to this bucket")
                return
            
            # Test PDF retrieval
            print("Retrieving PDF from storage...")
            try:
                pdf_content = await get_pdf_url(file_id)
                if pdf_content:
                    print("✅ Test passed: Successfully retrieved PDF content")
                else:
                    print("❌ Test failed: Retrieved PDF content is empty")
            except Exception as e:
                print(f"❌ PDF retrieval failed with error: {str(e)}")
                print("Please check:")
                print("1. The PDF file exists in storage")
                print("2. Your RLS policies allow downloads from this bucket")
                return
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        print(f"❌ Test failed with unexpected error: {str(e)}")

async def main():
    print("Starting database tests...")
    print("Make sure you have set the following environment variables:")
    print("- SUPABASE_URL")
    print("- SUPABASE_KEY")
    print("\nChecking environment variables...")
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ Missing required environment variables!")
        return
    
    print("✅ Environment variables found")
    await test_upload_and_retrieve()
    await test_pdf_storage()
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
