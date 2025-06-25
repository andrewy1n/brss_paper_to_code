from io import BytesIO
from typing import Union, Dict, Optional
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import httpx
from pydantic import BaseModel, HttpUrl
import tempfile
import os
import sys
import aiohttp
import json
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Add the current directory to Python path to ensure brss_paper_to_code is found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brss_paper_to_code.src.main import ProjectGenerator
import tempfile
from dotenv import load_dotenv
from db import (
    upload_pdf, 
    get_project_download_url, 
    store_project_info,
    upload_project,
    get_pdf_url
)

load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Allows all hosts
)

thread_pool = ThreadPoolExecutor(max_workers=4)

async def send_heartbeat(queue: asyncio.Queue):
    while True:
        await asyncio.sleep(20)
        await queue.put(f"data: {json.dumps({'status': 'heartbeat', 'message': 'Still processing...', 'timestamp': datetime.now().isoformat()})}\n\n")

async def run_in_thread(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, func, *args)

async def write_files(improved_blocks: Dict[str, str], temp_dir: str):
    for file_path, content in improved_blocks.items():
        full_path = os.path.join(temp_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        if content is None and file_path.endswith('/'):
            os.makedirs(full_path, exist_ok=True)
            continue
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

async def generate_progress_stream(generator: ProjectGenerator, temp_file_path: str, queue: asyncio.Queue):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            #await run_in_thread(generator.create_project_directory)
            project_id = str(uuid.uuid4())

            # Read paper
            await queue.put(f"data: {json.dumps({'status': 'reading_paper', 'message': 'Reading PDF file...'})}\n\n")
            paper_content = await run_in_thread(generator.read_paper, temp_file_path)
            
            # Generate plan
            await queue.put(f"data: {json.dumps({'status': 'generating_plan', 'message': 'Generating implementation plan...'})}\n\n")
            plan = await run_in_thread(generator.generate_plan, paper_content)
            
            # Implement code
            await queue.put(f"data: {json.dumps({'status': 'implementing_code', 'message': 'Implementing code...'})}\n\n")
            code_blocks = await run_in_thread(generator.implement_code, paper_content, plan)
            
            # Analyze code
            await queue.put(f"data: {json.dumps({'status': 'analyzing_code', 'message': 'Analyzing code...'})}\n\n")
            analysis = await run_in_thread(generator.analyze_code, paper_content, plan, code_blocks)
            
            # Improve code
            await queue.put(f"data: {json.dumps({'status': 'improving_code', 'message': 'Improving code based on analysis...'})}\n\n")
            improved_blocks = await run_in_thread(generator.improve_code, code_blocks, analysis)
            
            # Write files
            await queue.put(f"data: {json.dumps({'status': 'writing_files', 'message': 'Writing files...'})}\n\n")
            await write_files(improved_blocks, temp_dir)
            
            download_url = await upload_project(project_id, temp_dir)
            await store_project_info(project_id, download_url)
            
            # Send final result with file contents
            await queue.put(f"data: {json.dumps({'status': 'complete', 'message': 'Code generation complete', 'project_id': project_id, 'files': improved_blocks})}\n\n")
        
    except Exception as e:
        await queue.put(f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n")
        raise

async def stream_generator(generator: ProjectGenerator, temp_file_path: str):
    queue = asyncio.Queue()
    
    # Start heartbeat task
    heartbeat_task = asyncio.create_task(send_heartbeat(queue))
    
    try:
        # Start progress stream
        progress_task = asyncio.create_task(generate_progress_stream(generator, temp_file_path, queue))
        
        # Yield events from the queue
        while True:
            try:
                event = await queue.get()
                yield event
                
                # If we get a complete or error event, we're done
                if '"status":"complete"' in event or '"status":"error"' in event:
                    break
                    
            except asyncio.CancelledError:
                break
                
    finally:
        # Clean up tasks
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

@app.post("/upload")
async def upload(
    file: Optional[UploadFile] = File(None),
    pdf_url: Optional[str] = Form(None)
):
    # Check if we have a valid file upload
    has_file = file is not None and file.filename and file.filename.endswith('.pdf')
    
    # Check if we have a valid URL
    has_url = pdf_url is not None and pdf_url.strip() != ""
    
    if not has_file and not has_url:
        raise HTTPException(status_code=400, detail="Either file upload or PDF URL must be provided")
    
    if has_file and has_url:
        raise HTTPException(status_code=400, detail="Cannot provide both file upload and PDF URL")
    
    try:
        file_id = str(uuid.uuid4())
        
        # Create a temporary file to store the PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            if has_file:
                content = await file.read()
                temp_file.write(content)
            elif has_url:
                async with aiohttp.ClientSession() as session:
                    async with session.get(pdf_url) as response:
                        if response.status != 200:
                            raise HTTPException(status_code=400, detail="Failed to download PDF from URL")
                        content = await response.read()
                        temp_file.write(content)
            
            temp_file_path = temp_file.name
        
        try:
            # Upload to Supabase storage using file path
            await upload_pdf(file_id, temp_file_path)
            
            return {"file_id": file_id, "message": "PDF uploaded successfully"}
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/generate/{file_id}")
async def generate_code(file_id: str):
    temp_file_path = None
    try:
        # Get PDF from Supabase storage
        pdf_url = await get_pdf_url(file_id)
        pdf_content = None

        async with aiohttp.ClientSession() as session:
            async with session.get(pdf_url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail="Failed to download PDF from URL")
                pdf_content = await response.read()
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name
        
        # Initialize the project generator
        generator = ProjectGenerator()
        
        # Create a background task to clean up the file after streaming is complete
        async def cleanup_file():
            try:
                await asyncio.sleep(1)  # Give a small delay to ensure file is not being read
                if temp_file_path and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            except Exception as e:
                print(f"Error cleaning up file: {e}")
        
        # Start cleanup task
        asyncio.create_task(cleanup_file())
        
        # Return streaming response
        return StreamingResponse(
            stream_generator(generator, temp_file_path),
            media_type="text/event-stream"
        )
            
    except Exception as e:
        if 'generator' in locals():
            generator.cleanup()
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{project_id}")
async def download_project(project_id: str):
    download_url = await get_project_download_url(project_id)
    if not download_url:
        raise HTTPException(status_code=404, detail="Project not found")

    async with httpx.AsyncClient() as client:
        file_response = await client.get(download_url)

        if file_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch file from storage")

        content_type = file_response.headers.get("content-type", "application/octet-stream")

        # Step 3: Stream the file back to the client
        return StreamingResponse(
            BytesIO(file_response.content),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={project_id}.zip"}
        )