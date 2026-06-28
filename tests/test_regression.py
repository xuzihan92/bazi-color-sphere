"""
回归测试 — 金标准锁定
═══════════════════════════════════════════════════════════════
⚠️  警告：这些测试是「锁止阀」，一旦失败代表引擎行为发生了变化。
    任何改变引擎输出的修改，必须先经元清/存真审批，再更新 GOLD 值。
═══════════════════════════════════════════════════════════════
"""
import pytest

# 梓涵八字金标准（来自 conftest.py）
XUZIHAN_BAZI = {
    "year": {"gan": "壬", "zhi": "申"},
    "month": {"gan": "己", "zhi": "酉"},
    "day": {"gan": "丁", "zhi": "未"},
    "hour": {"gan": "丙", "zhi": "午"},
}
XUZIHAN_GOLD = {
    "hex": "#7C202F",
    "H_min": 345.0,
    "H_max": 355.0,
    "H_exact": 350.1998306632618,
    "T": 4575.0,
    "S": 0.583,
    "L": 0.309,
}


class TestRegressionXuzihan:
    """梓涵本命（壬申 己酉 丁未 丙午）金标准回归测试组"""

    def test_regression_hex_exact(self, engine):
        """
        R-001: 梓涵本命色十六进制精确匹配
        金标准: #7C202F（深茜红，H=350°，CCT≈4575K）
        """
        result = engine.compute_birth_color(XUZIHAN_BAZI)
        assert result["hsl_hex"] == XUZIHAN_GOLD["hex"], (
            f"本命色 hex 偏移！期望 {XUZIHAN_GOLD['hex']}，实际 {result['hsl_hex']}\n"
            f"这意味着引擎计算逻辑或 JSON 数据发生了变化，需走审批流程。"
        )

    def test_regression_hue_zone(self, engine):
        """
        R-002: 色相 H 在火属性红色区间内
        金标准区间: 345°~355°（允许 ±5° 浮动容差）
        """
        result = engine.compute_birth_color(XUZIHAN_BAZI)
        h = result["H"]
        assert h is not None, "本命色 H 不应为 None（非全土命）"
        assert XUZIHAN_GOLD["H_min"] <= h <= XUZIHAN_GOLD["H_max"], (
            f"色相 H={h:.2f}° 超出金标准区间 "
            f"[{XUZIHAN_GOLD['H_min']}°, {XUZIHAN_GOLD['H_max']}°]"
        )

    def test_regression_hue_precise(self, engine):
        """
        R-003: 色相 H 精确值（允许浮点误差 ±0.001°）
        """
        result = engine.compute_birth_color(XUZIHAN_BAZI)
        assert abs(result["H"] - XUZIHAN_GOLD["H_exact"]) < 0.001, (
            f"色相精确值漂移: 期望 {XUZIHAN_GOLD['H_exact']:.6f}°，"
            f"实际 {result['H']:.6f}°"
        )

    def test_regression_color_temperature(self, engine):
        """
        R-004: 色温 T 在合理范围（金标准 4575K）
        """
        result = engine.compute_birth_color(XUZIHAN_BAZI)
        t = result["T"]
        assert 4000 <= t <= 5000, (
            f"色温 T={t}K 超出合理范围 [4000K, 5000K]，金标准 {XUZIHAN_GOLD['T']}K"
        )

    def test_regression_saturation(self, engine):
        """
        R-005: 饱和度 S 精确值（允许 ±0.005 浮点误差）
        """
        result = engine.compute_birth_color(XUZIHAN_BAZI)
        assert abs(result["S"] - XUZIHAN_GOLD["S"]) < 0.005, (
            f"饱和度偏移: 期望 {XUZIHAN_GOLD['S']}, 实际 {result['S']}"
        )

    def test_regression_lightness(self, engine):
        """
        R-006: 明度 L 精确值（允许 ±0.005 浮点误差）
        """
        result = engine.compute_birth_color(XUZIHAN_BAZI)
        assert abs(result["L"] - XUZIHAN_GOLD["L"]) < 0.005, (
            f"明度偏移: 期望 {XUZIHAN_GOLD['L']}, 实际 {result['L']}"
        )

    def test_regression_fire_dominant(self, engine):
        """
        R-007: 五行分布中火(丙/丁)占比最高
        梓涵日主丁火，时柱丙午，火应主导
        """
        report = engine.compute_lifetime_color({"birth": XUZIHAN_BAZI})
        balance = report["wuxing_balance"]
        fire_ratio = balance.get("火", 0)
        # 火应 > 其他任何一行
        for element, ratio in balance.items():
            if element != "火":
                assert fire_ratio >= ratio, (
                    f"火({fire_ratio:.3f}) 应不低于 {element}({ratio:.3f})，"
                    f"五行分布: {balance}"
                )
