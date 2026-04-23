#!/bin/bash
# mathcoe_backend - 提交代码到 GitHub
# 使用方式: ./push.sh "提交消息" 或 ./push.sh（使用默认消息）

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=== mathcoe_backend Git 提交 ==="
echo "项目目录: $PROJECT_DIR"
echo ""

# 获取提交消息
COMMIT_MSG="${1:-更新代码 $(date '+%Y-%m-%d %H:%M')}"

# 显示当前状态
echo "当前修改文件:"
git status --short
echo ""

# 添加所有文件
echo "添加文件到暂存区..."
git add -A

# 检查是否有需要提交的内容
if git diff --cached --quiet; then
    echo "没有需要提交的内容"
    exit 0
fi

# 显示将要提交的内容
echo "将要提交的内容:"
git diff --cached --stat
echo ""

# 提交
echo "创建提交: $COMMIT_MSG"
git commit -m "$COMMIT_MSG"

# 推送
echo "推送到 GitHub..."
git push origin main

echo ""
echo "✅ 提交完成!"
echo "远程仓库: https://github.com/cnzhangsheng/mathcoe_backend"