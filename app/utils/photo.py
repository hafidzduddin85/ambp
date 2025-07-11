# app/utils/photo.py
import io
import os
from PIL import Image
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials
import json
import logging

def get_drive_service():
    """Get Google Drive service"""
    try:
        creds_json_str = os.getenv("GOOGLE_CREDS_JSON")
        if not creds_json_str:
            raise RuntimeError("GOOGLE_CREDS_JSON not set")
        
        creds_json = json.loads(creds_json_str)
        if "private_key" in creds_json:
            creds_json["private_key"] = creds_json["private_key"].replace("\\n", "\n")
        
        credentials = Credentials.from_service_account_info(
            creds_json, 
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        logging.error(f"Error creating Drive service: {e}")
        return None

def resize_and_convert_image(image_file, max_size=(800, 600), quality=85):
    """Resize image and convert to WebP format"""
    try:
        # Open image
        image = Image.open(image_file)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # Calculate new size maintaining aspect ratio
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save as WebP
        output = io.BytesIO()
        image.save(output, format='WEBP', quality=quality, optimize=True)
        output.seek(0)
        
        return output
    except Exception as e:
        logging.error(f"Error resizing image: {e}")
        return None

def upload_to_drive(image_data, filename, asset_id):
    """Upload image to Google Drive"""
    try:
        service = get_drive_service()
        if not service:
            return None
        
        # Use shared drive folder ID: 0ANzABR32MM4AUk9PVA
        folder_id = "0ANzABR32MM4AUk9PVA"
        
        # Upload file
        file_metadata = {
            'name': f"{asset_id}_{filename}.webp",
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(
            image_data, 
            mimetype='image/webp',
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,webViewLink,webContentLink'
        ).execute()
        
        # Make file publicly viewable
        service.permissions().create(
            fileId=file['id'],
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()
        
        # Return direct image URL
        return f"https://drive.google.com/uc?id={file['id']}"
        
    except Exception as e:
        logging.error(f"Error uploading to Drive: {e}")
        return None

def get_or_create_folder(service, folder_name):
    """Get or create folder in Google Drive"""
    try:
        # Search for existing folder
        results = service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
            fields="files(id, name)"
        ).execute()
        
        folders = results.get('files', [])
        
        if folders:
            return folders[0]['id']
        
        # Create new folder
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        return folder['id']
        
    except Exception as e:
        logging.error(f"Error creating folder: {e}")
        return None

def delete_from_drive(image_url):
    """Delete image from Google Drive"""
    try:
        if not image_url or 'drive.google.com' not in image_url:
            return False
        
        # Extract file ID from URL
        file_id = image_url.split('id=')[1] if 'id=' in image_url else None
        if not file_id:
            return False
        
        service = get_drive_service()
        if not service:
            return False
        
        service.files().delete(fileId=file_id).execute()
        return True
        
    except Exception as e:
        logging.error(f"Error deleting from Drive: {e}")
        return False