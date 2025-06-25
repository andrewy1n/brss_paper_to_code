from datetime import datetime, timedelta, timezone
import os
import shutil
import zipfile
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

async def store_project_info(project_id: str, download_url: str):
    try:
        data = {
            "id": project_id,
            "download_url": download_url,
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        }
        
        result = supabase.table("projects").insert(data).execute()
        return result.data
    except Exception as e:
        print(f"Error storing project info: {e}")
        raise

async def upload_pdf(file_id: str, pdf_path: str):
    try:
        with open(pdf_path, 'rb') as f:
            supabase.storage.from_('pdf').upload(
                f"{file_id}.pdf",
                f.read(),
                {"content-type": "application/pdf"}
            )
        return True
    except Exception as e:
        print(f"Error uploading PDF to Supabase Storage: {e}")
        raise

async def get_pdf_url(file_id: str):
    try:
        signed_url_data = supabase.storage.from_('pdf').create_signed_url(f"{file_id}.pdf", 60 * 60 * 24)  # valid for 24 hours
        url = signed_url_data.get("signedURL")
        return url
    except Exception as e:
        print(f"Error getting PDF URL: {e}")
        raise

async def upload_project(project_id: str, project_path: str):
    try:
        # Create zip file
        zip_path = f"{project_path}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(project_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_path)
                    zipf.write(file_path, arcname)
        
        with open(zip_path, 'rb') as f:
            supabase.storage.from_('project-code').upload(
                f"{project_id}.zip",
                f.read(),
                {"content-type": "application/zip"}
            )
        
        signed_url_data = supabase.storage.from_('project-code').create_signed_url(f"{project_id}.zip", 60 * 60 * 24)  # valid for 24 hours
        url = signed_url_data.get("signedURL")
        
        os.remove(zip_path)
        shutil.rmtree(project_path)
        
        return url
    except Exception as e:
        print(f"Error uploading to Supabase Storage: {e}")
        raise

async def get_project_download_url(project_id: str):
    try:
        result = supabase.table("projects").select("download_url").eq("id", project_id).execute()
        if not result.data:
            return None
        return result.data[0]["download_url"]
    except Exception as e:
        print(f"Error retrieving project info: {e}")
        raise