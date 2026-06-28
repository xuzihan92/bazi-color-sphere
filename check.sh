#!/bin/bash
# ============================================================
# 八字色彩引擎 — 代码质量一键检查
# 用法: bash check.sh [lint|test|all]
#   无参数默认跑 all（lint + test）
#
# 绝对路径: E:/AI/U-Claw/data/.openclaw/workspace-team/玄学部/八字色彩/check.sh
# ⚠️  520/313 双环境通用 — 脚本内路径均已用绝对路径，禁止改用相对路径
#
# 行知阁技术部 · CI/CD v1.0
# ============================================================
# === 配置 ===
ENGINE_FILE="wuxing_sphere_v2.1.py"
TEST_DIR="tests"
FLAKE8_CONFIG=".flake8"
PYTHON_BIN="${WB_PYTHON_BIN:-python}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass_count=0
fail_count=0

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((pass_count++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((fail_count++))
}

run_lint() {
    echo ""
    echo "=========================================="
    echo "  📋 Lint 检查"
    echo "=========================================="

    # flake8
    echo -n "flake8 ................... "
    FLAKE8_OUT=$(flake8 --config="$FLAKE8_CONFIG" "$ENGINE_FILE" 2>&1) || true
    if [ -z "$FLAKE8_OUT" ]; then
        check_pass "flake8: 0 errors"
    else
        check_fail "flake8: 有错误"
        echo "$FLAKE8_OUT"
    fi

    # black
    echo -n "black --check ........... "
    BLACK_OUT=$(black --check "$ENGINE_FILE" 2>&1) || true
    if echo "$BLACK_OUT" | grep -q "would reformat\|would be reformatted"; then
        check_fail "black: 格式不一致，请运行 bash format.sh"
    else
        check_pass "black: 格式一致"
    fi

    # isort
    echo -n "isort --check-only ...... "
    ISORT_OUT=$(isort --check-only "$ENGINE_FILE" 2>&1) || true
    if echo "$ISORT_OUT" | grep -q "would be reordered\|ERROR"; then
        check_fail "isort: 导入顺序不对，请运行 bash format.sh"
    else
        check_pass "isort: 导入顺序正确"
    fi
}

run_test() {
    echo ""
    echo "=========================================="
    echo "  🧪 测试运行"
    echo "=========================================="

    # pytest
    echo -n "pytest .................. "
    PYTEST_OUT=$(pytest "$TEST_DIR/" -v --tb=short 2>&1) || true
    if echo "$PYTEST_OUT" | grep -q "failed"; then
        check_fail "pytest: 有失败"
        echo "$PYTEST_OUT" | grep -E "FAILED|ERROR|failed|error" || true
    else
        check_pass "pytest: 全部通过"
    fi

    # 回归测试（金标准）
    echo -n "回归测试 (梓涵本命) ..... "
    REGRESSION=$(pytest "$TEST_DIR/test_regression.py" -v --tb=line -q 2>&1) || true
    if echo "$REGRESSION" | grep -q "passed"; then
        check_pass "回归测试: 金标准 #7C202F 锁定"
    else
        check_fail "回归测试: 金标准 #7C202F 偏离！立即阻断"
    fi
}

run_all() {
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║  八字色彩引擎 · 代码质量检查             ║"
    echo "║  行知阁技术部 · CI/CD v1.0              ║"
    echo "╚══════════════════════════════════════════╝"

    run_lint
    run_test

    echo ""
    echo "=========================================="
    echo "  检查结果汇总"
    echo "=========================================="
    echo -e "  通过: ${GREEN}${pass_count}${NC}  失败: ${RED}${fail_count}${NC}"

    if [ $fail_count -gt 0 ]; then
        echo ""
        echo -e "${RED}⛔ 质量门禁未通过，不得进入审言审查。${NC}"
        echo -e "${RED}   请修复上方 ❌ 标记的项后重试。${NC}"
        exit 1
    else
        echo ""
        echo -e "${GREEN}🎉 全部通过！可提交审言审查。${NC}"
        echo ""
        echo "  下一步：在协作链待办板更新回执状态"
    fi
}

case "${1:-all}" in
    lint) run_lint ;;
    test) run_test ;;
    all)  run_all ;;
    *)
        echo "用法: bash check.sh [lint|test|all]"
        exit 1
        ;;
esac
