"""Google Drive upload helpers."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


@dataclass(frozen=True)
class DriveUploadResult:
    file_id: str
    name: str
    web_view_link: Optional[str]
    web_content_link: Optional[str]


def _load_service_account_info() -> dict:
    json_value = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if json_value:
        return json.loads(json_value)

    json_b64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64")
    if json_b64:
        decoded = base64.b64decode(json_b64).decode("utf-8")
        return json.loads(decoded)

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path:
        with open(credentials_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    raise RuntimeError(
        "Google service account credentials are not set. Provide "
        "GOOGLE_SERVICE_ACCOUNT_JSON, GOOGLE_SERVICE_ACCOUNT_JSON_BASE64, "
        "or GOOGLE_APPLICATION_CREDENTIALS."
    )


def build_drive_service():
    service_account_info = _load_service_account_info()
    creds = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES,
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def upload_file_to_drive(
    file_path: Path,
    folder_id: Optional[str] = None,
    make_public: Optional[bool] = None,
    shared_drive_id: Optional[str] = None,
) -> DriveUploadResult:
    if make_public is None:
        make_public = os.getenv("GDRIVE_PUBLIC", "false").lower() == "true"
    if shared_drive_id is None:
        shared_drive_id = os.getenv("GDRIVE_SHARED_DRIVE_ID")

    service = build_drive_service()
    metadata = {"name": file_path.name}
    if folder_id:
        metadata["parents"] = [folder_id]

    media = MediaFileUpload(str(file_path), mimetype="video/mp4", resumable=True)
    create_kwargs = {
        "body": metadata,
        "media_body": media,
        "fields": "id, name, webViewLink, webContentLink",
    }
    if shared_drive_id:
        create_kwargs["supportsAllDrives"] = True

    created = service.files().create(**create_kwargs).execute()

    if make_public:
        perm_kwargs = {
            "fileId": created["id"],
            "body": {"type": "anyone", "role": "reader"},
        }
        if shared_drive_id:
            perm_kwargs["supportsAllDrives"] = True
        service.permissions().create(**perm_kwargs).execute()

        get_kwargs = {
            "fileId": created["id"],
            "fields": "id, name, webViewLink, webContentLink",
        }
        if shared_drive_id:
            get_kwargs["supportsAllDrives"] = True
        created = service.files().get(**get_kwargs).execute()

    return DriveUploadResult(
        file_id=created["id"],
        name=created.get("name") or file_path.name,
        web_view_link=created.get("webViewLink"),
        web_content_link=created.get("webContentLink"),
    )
