"""Google Drive upload helpers."""

from __future__ import annotations

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


def build_drive_service():
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS is not set.")

    creds = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=SCOPES,
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def upload_file_to_drive(
    file_path: Path,
    folder_id: Optional[str] = None,
    make_public: Optional[bool] = None,
) -> DriveUploadResult:
    if make_public is None:
        make_public = os.getenv("GDRIVE_PUBLIC", "false").lower() == "true"

    service = build_drive_service()
    metadata = {"name": file_path.name}
    if folder_id:
        metadata["parents"] = [folder_id]

    media = MediaFileUpload(str(file_path), mimetype="video/mp4", resumable=True)
    created = (
        service.files()
        .create(body=metadata, media_body=media, fields="id, name, webViewLink, webContentLink")
        .execute()
    )

    if make_public:
        service.permissions().create(
            fileId=created["id"],
            body={"type": "anyone", "role": "reader"},
        ).execute()
        created = (
            service.files()
            .get(fileId=created["id"], fields="id, name, webViewLink, webContentLink")
            .execute()
        )

    return DriveUploadResult(
        file_id=created["id"],
        name=created.get("name") or file_path.name,
        web_view_link=created.get("webViewLink"),
        web_content_link=created.get("webContentLink"),
    )
