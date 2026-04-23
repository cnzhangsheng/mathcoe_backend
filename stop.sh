#!/bin/bash
# Kangaroo Math Brain Backend 停止脚本
# 使用方式: ./stop.sh

echo "=== 停止 Kangaroo Math Brain Backend ==="

# 检查端口是否被占用
if lsof -i :8000 > /dev/null 2>&1; then
    PID=$(lsof -i :8000 -t)
    echo "停止进程 PID: $PID"
    kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null
    sleep 1
    echo "✅ 服务已停止"
else
    echo "端口 8000 无服务运行"
fi