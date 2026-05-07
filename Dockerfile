# 最新稳定（推荐 👍 生产环境首选）
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

WORKDIR /app

# 安装 WeasyPrint 必需系统依赖（Debian 12 100% 兼容）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件 → 利用 Docker 缓存，加速构建
COPY pyproject.toml ./

# 安装项目依赖（不缓存，减小镜像体积）
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# 复制项目代码
COPY app/ app/

# 创建日志/存储目录（权限安全）
RUN mkdir -p logs storage/exam_papers \
    && chmod -R 755 logs storage

# 暴露端口
EXPOSE 8000

# 生产级启动命令（官方镜像最佳实践）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]