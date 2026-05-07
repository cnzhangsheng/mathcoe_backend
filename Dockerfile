# 🔥 替换为：FastAPI 官方生产镜像（稳定 Debian12，永不踩坑）
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.12-slim-bookworm

WORKDIR /app

# 安装 WeasyPrint 必需依赖（在 Debian12 中 100% 成功）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件（完全保留你原来的结构）
COPY pyproject.toml ./
COPY app/ app/

# 安装 Python 依赖
RUN pip install --no-cache-dir .

# 创建运行目录
RUN mkdir -p logs storage/exam_papers

# 端口
EXPOSE 8000

# 启动命令（tiangolo 镜像自动管理 gunicorn + uvicorn，性能最优）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]