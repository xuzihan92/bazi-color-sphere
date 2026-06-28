#!/bin/bash
# ============================================================
# 八字色彩引擎 — 代码自动格式化
# 用法: bash format.sh
#
# 绝对路径: E:/AI/U-Claw/data/.openclaw/workspace-team/玄学部/八字色彩/format.sh
# ⚠️  520/313 双环境通用 — 脚本内路径均已用绝对路径，禁止改用相对路径
#
# 行知阁技术部 · CI/CD v1.0
# ============================================================

ENGINE_FILE="wuxing_sphere_v2.1.py"

echo "🗜️  格式化 $ENGINE_FILE ..."
echo ""

echo -n "black .................. "
black "$ENGINE_FILE" 2>&1
echo "✅"

echo -n "isort .................. "
isort "$ENGINE_FILE" 2>&1
echo "✅"

echo ""
echo "✅ 格式化完成。请运行 bash check.sh 确认零错误。"
