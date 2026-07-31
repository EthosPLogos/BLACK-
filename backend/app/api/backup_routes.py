import io
import json
import zipfile
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.config import (
    APPROVALS_PATH,
    AUDIT_LOG_PATH,
    BACKEND_VERSION,
    MEMORY_PATH,
    SCHEDULE_PATH,
)

router = APIRouter(prefix="/api/backup", tags=["backup"])

_BACKUP_FILES = {
    "black_memory.json": MEMORY_PATH,
    "black_schedule.json": SCHEDULE_PATH,
    "black_audit.jsonl": AUDIT_LOG_PATH,
    "black_approvals.json": APPROVALS_PATH,
}


@router.get("/info")
def backup_info():
    files = []
    for name, path in _BACKUP_FILES.items():
        if path.exists():
            stat = path.stat()
            files.append({
                "name": name,
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    return {"files": files, "version": BACKEND_VERSION}


@router.get("/download")
def download_backup():
    buf = io.BytesIO()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        included = []
        for name, path in _BACKUP_FILES.items():
            if path.exists():
                zf.write(path, name)
                included.append(name)

        manifest = {
            "version": BACKEND_VERSION,
            "created": datetime.now().isoformat(),
            "files": included,
        }
        zf.writestr("backup_manifest.json", json.dumps(manifest, indent=2))

    buf.seek(0)
    filename = f"black_backup_{timestamp}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/restore")
async def restore_backup(file: UploadFile = File(...)):
    if not (file.filename or "").endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip backup")

    content = await file.read()

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            if "backup_manifest.json" not in zf.namelist():
                raise HTTPException(status_code=400, detail="Not a valid BLACK backup — missing manifest")

            manifest = json.loads(zf.read("backup_manifest.json"))
            restored = []

            for name, path in _BACKUP_FILES.items():
                if name in zf.namelist():
                    path.write_bytes(zf.read(name))
                    restored.append(name)

            return {
                "restored": restored,
                "backup_version": manifest.get("version"),
                "backup_created": manifest.get("created"),
                "message": f"Restored {len(restored)} file(s). Restart the backend to apply.",
            }
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid or corrupted zip file")
