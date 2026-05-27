"""
Kangaroo Math Brain - FastAPI Application Entry Point
"""
import logging
import logging.config
import os
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sqlalchemy import select
from fastapi.responses import HTMLResponse

from app.api.deps import DBSession
from app.api.v1.router import router as api_router
from app.core.config import settings
from app.models.content import Content
from app.utils.content import enhance_content_html


# 配置日志 - 在 worker 进程中也生效
logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, "app.log")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "default",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": log_file,
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "sqlalchemy": {
            "level": "WARNING",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("应用启动完成")
    yield
    logger.info("应用关闭")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="小学数学思维后端服务",
    lifespan=lifespan,
)

# CORS configuration for WeChat Mini Program
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


# ============ 异常处理器 ============

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理器 - 记录 HTTP 错误"""
    logger.error(f"HTTP异常: {exc.status_code} - {exc.detail} | 路径: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器 - 记录未捕获的异常"""
    error_msg = f"{type(exc).__name__}: {str(exc)}"
    logger.error(f"未捕获异常: {error_msg} | 路径: {request.url.path}")
    logger.error(f"调用栈:\n{traceback.format_exc()}")

    # 开发环境返回详细错误信息
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "detail": error_msg,
                "type": type(exc).__name__,
                "path": request.url.path,
                "traceback": traceback.format_exc().split("\n")
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": settings.app_version}


@app.get("/content/{slug}")
async def render_content_page(slug: str, db: DBSession):
    """外部浏览器访问：渲染已发布的内容为完整 HTML 页面"""
    result = await db.execute(
        select(Content).where(Content.slug == slug, Content.status == "published")
    )
    content = result.scalar_one_or_none()

    if not content:
        return HTMLResponse("<h1>404 - 内容不存在</h1>", status_code=404)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>{content.title} - 小学数学思维</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8f8f8; color: #333; line-height: 1.8; }}
.container {{ max-width: 800px; margin: 0 auto; padding: 40px 32px; }}
.header {{ margin-bottom: 32px; }}
.header h1 {{ font-size: 28px; color: #333; }}
.meta {{ font-size: 14px; color: #999; margin-top: 8px; }}
.content {{ font-size: 16px; color: #444; }}
.content p {{ margin-bottom: 16px; }}
.content img {{ max-width: 100%; height: auto; border-radius: 8px; }}
.footer {{ margin-top: 48px; padding-top: 24px; border-top: 1px solid #eee; text-align: center; font-size: 13px; color: #999; }}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>{content.title}</h1>
<div class="meta">更新时间：{content.updated_at.strftime('%Y-%m-%d %H:%M')}</div>
</div>
<div class="content">{enhance_content_html(content.content)}</div>
<div class="footer">由 小学数学思维 提供</div>
</div>
</body>
</html>"""
    return HTMLResponse(content=html)