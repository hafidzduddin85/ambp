import io
import os
import json
import logging
import requests
from PIL import Image
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request

# Constants
DRIVE_SCOPE = ['https://www.googleapis.com/auth/drive.file']
MAX_IMAGE_SIZE = (800, 600)
WEBP_QUALITY = 85


def get_access_token():
    """Get Google Drive access token from service account."""
    try:
        creds_json = json.loads(os.getenv("GOOGLE_CREDS_JSON", "{}"))
        if "private_key" in creds_json:
            creds_json["private_key"] = creds_json["private_key"].replace("\\n", "\n")
        credentials = Credentials.from_service_account_info(creds_json, scopes=DRIVE_SCOPE)
        credentials.refresh(Request())
        return credentials.token
    except Exception as e:
        logging.error(f"[Drive] Failed to obtain access token: {e}")
        return None


def resize_and_convert_image(image_file, max_size=MAX_IMAGE_SIZE, quality=WEBP_QUALITY):
    """Resize image and convert to WebP format."""
    try:
        image = Image.open(image_file)
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')

        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        output = io.BytesIO()
        image.save(output, format='WEBP', quality=quality, optimize=True)
        output.seek(0)
        return output
    except Exception as e:
        logging.error(f"[Image] Failed to process image: {e}")
        return None


def upload_to_drive(image_data, filename, asset_id):
    """Upload an image to Google Drive using resumable upload."""
    access_token = get_access_token()
    if not access_token:
        return None

    folder_id = os.getenv("DRIVE_FOLDER_ID")
    if not folder_id or folder_id.startswith("0A"):
        logging.error("[Drive] Invalid or missing DRIVE_FOLDER_ID — must be a real folder, not root ID (0A...)")
        return None

    logging.info(f"[Drive] Uploading to folder ID: {folder_id}")

    # Step 1: Start resumable upload
    upload_url = _initiate_upload(access_token, filename, asset_id, image_data, folder_id)
    if not upload_url:
        return None

    # Step 2: Upload the actual image data
    file_id = _upload_file_data(upload_url, image_data)
    if not file_id:
        return None

    # Step 3: Make file public
    _set_public_permission(access_token, file_id)

    return f"https://drive.google.com/uc?id={file_id}"


def _initiate_upload(access_token, filename, asset_id, image_data, folder_id):
    """Start a resumable upload session with Google Drive."""
    file_metadata = {
        'name': f"{asset_id}_{filename}.webp",
        'parents': [folder_id]
    }

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Upload-Content-Type': 'image/webp',
        'X-Upload-Content-Length': str(len(image_data.getvalue()))
    }

    try:
        res = requests.post(
            'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable',
            headers=headers,
            json=file_metadata,
            timeout=30
        )

        if res.status_code == 200:
            return res.headers.get('Location')
        else:
            logging.error(f"[Drive] Failed to initiate upload: {res.status_code} - {res.text}")
            return None
    except Exception as e:
        logging.error(f"[Drive] Error initiating upload session: {e}")
        return None


def _upload_file_data(upload_url, image_data):
    """Upload the binary file content to Google Drive."""
    image_data.seek(0)
    headers = {
        'Content-Type': 'image/webp',
        'Content-Length': str(len(image_data.getvalue()))
    }

    try:
        res = requests.put(
            upload_url,
            headers=headers,
            data=image_data.getvalue(),
            timeout=60
        )

        if res.status_code in [200, 201]:
            return res.json().get('id')
        else:
            logging.error(f"[Drive] Upload failed: {res.status_code} - {res.text}")
            return None
    except Exception as e:
        logging.error(f"[Drive] Error uploading file data: {e}")
        return None


def _set_public_permission(access_token, file_id):
    """Set file to be publicly accessible."""
    try:
        res = requests.post(
            f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            },
            json={'role': 'reader', 'type': 'anyone'},
            timeout=30
        )
        if res.status_code not in [200, 204]:
            logging.warning(f"[Drive] Failed to set public permission: {res.status_code} - {res.text}")
    except Exception as e:
        logging.error(f"[Drive] Permission setting error: {e}")


def delete_from_drive(image_url):
    """Delete a file from Google Drive by public link."""
    try:
        if not image_url or 'drive.google.com' not in image_url:
            return False

        file_id = image_url.split('id=')[1] if 'id=' in image_url else None
        if not file_id:
            return False

        access_token = get_access_token()
        if not access_token:
            return False

        res = requests.delete(
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=30
        )

        return res.status_code == 204

    except Exception as e:
        logging.error(f"[Drive] Error deleting file: {e}")
        return False
