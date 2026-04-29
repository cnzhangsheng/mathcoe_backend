# Kangaroo Math Brain Backend

袋鼠数学助理后端服务 - FastAPI + PostgreSQL

## 快速开始

```bash
# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env

# 启动服务
uvicorn app.main:app --reload
```

## API 文档

启动服务后访问 http://localhost:8000/docs 查看 Swagger UI 文档。