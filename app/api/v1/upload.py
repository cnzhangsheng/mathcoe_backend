"""
File upload API
"""
import logging
import os
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

BASE_UPLOAD_DIR = "app/static/uploads"
os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)

@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    folder: str = Query("", description="子目录，如 banners"),
):
    """上传图片"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只支持图片文件")

    # 构建上传目录
    STATIC_DIR = "app/static"
    if folder:
        upload_dir = os.path.join(STATIC_DIR, folder)
        url_prefix = folder
    else:
        upload_dir = BASE_UPLOAD_DIR
        url_prefix = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # 生成唯一文件名
    ext = file.filename.split(".")[-1] if file.filename else "jpg"
    filename = f"{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(upload_dir, filename)

    # 保存文件
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # 返回绝对URL
    base = settings.server_host.rstrip("/")
    url = f"{base}/api/v1/static/{url_prefix}/{filename}"
    logger.info(f"图片上传: folder={folder}, filename={filename}, size={len(content)}bytes, url={url}")
    return {"url": url, "filename": filename}


@router.get("/static/{full_path:path}")
async def get_uploaded_file(full_path: str):
    """获取上传的文件"""
    allowed_dir = os.path.realpath("app/static")
    filepath = os.path.realpath(os.path.join(allowed_dir, full_path))
    if not filepath.startswith(allowed_dir):
        raise HTTPException(status_code=400, detail="非法路径")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(filepath)