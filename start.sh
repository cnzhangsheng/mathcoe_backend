#!/bin/bash
# Kangaroo Math Brain Backend 启动脚本
# 使用方式: ./start.sh

set -e

# 项目目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Kangaroo Math Brain Backend ==="
echo "项目目录: $PROJECT_DIR"

# 进入项目目录
cd "$PROJECT_DIR"

# 检查 venv 是否存在
if [ ! -d ".venv" ]; then
    echo "错误: .venv 目录不存在，请先创建虚拟环境"
    exit 1
fi

# 安装缺失的依赖（如果有）
echo "检查依赖..."
uv pip install python-multipart --python .venv/bin/python --quiet 2>/dev/null || true

# 检查端口是否被占用
if lsof -i :8000 > /dev/null 2>&1; then
    echo "端口 8000 已被占用，停止现有进程..."
    lsof -i :8000 -t | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# 启动服务
echo "启动 uvicorn 服务..."
echo "服务地址: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo ""

# 使用 nohup 在后台运行，日志输出到 logs 目录
mkdir -p logs
nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/server.log 2>&1 &

# 等待服务启动
sleep 2

# 检查服务是否成功启动
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 服务启动成功!"
    curl -s http://localhost:8000/health
    echo ""
else
    echo "❌ 服务启动失败，请检查日志: logs/server.log"
    exit 1
fi

# 显示进程信息
echo "进程 PID: $(lsof -i :8000 -t)"
echo ""
echo "停止服务: kill $(lsof -i :8000 -t)"
echo "查看日志: tail -f logs/server.log"