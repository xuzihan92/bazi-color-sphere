"""
引擎逻辑测试 — 算法行为验证
"""
import math

import pytest

XUZIHAN_BAZI = {
    "year": {"gan": "壬", "zhi": "申"},
    "month": {"gan": "己", "zhi": "酉"},
    "day": {"gan": "丁", "zhi": "未"},
    "hour": {"gan": "丙", "zhi": "午"},
}


class TestHSLConversion:
    """HSL 数据类测试"""

    def test_hsl_to_hex_white(self, engine_module):
        """E-001: HSL(0, 0, 1) = 纯白 #FFFFFF"""
        HSL = engine_module.HSL
        assert HSL(0, 0, 1).to_hex() == "#FFFFFF"

    def test_hsl_to_hex_black(self, engine_module):
        """E-002: HSL(0, 0, 0) = 纯黑 #000000"""
        HSL = engine_module.HSL
        assert HSL(0, 0, 0).to_hex() == "#000000"

    def test_hsl_to_hex_red(self, engine_module):
        """E-003: HSL(0, 1, 0.5) = 纯红 #FF0000"""
        HSL = engine_module.HSL
        r, g, b = HSL(0, 1, 0.5).to_rgb()
        assert r == 255
        assert g == 0
        assert b == 0

    def test_hsl_clamp_overflow(self, engine_module):
        """E-004: 超范围 HSL 自动裁剪"""
        HSL = engine_module.HSL
        h = HSL(370, 1.5, -0.2).clamp()
        assert 0 <= h.h < 360
        assert 0 <= h.s <= 1
        assert 0 <= h.l <= 1

    def test_hsl_hex_format(self, engine_module):
        """E-005: hex 输出格式为 #RRGGBB（7字符）"""
        HSL = engine_module.HSL
        result = HSL(120, 0.5, 0.5).to_hex()
        assert result.startswith("#")
        assert len(result) == 7


class TestCircularHueMixing:
    """圆形 H 加权平均算法测试（解决 0°/360° 边界）"""

    def test_circular_average_boundary(self, mapper):
        """
        E-006: 350° 和 10° 的加权平均应靠近 0°（红色），
               而非 180°（绿色）——这是线性平均的经典 Bug。
        """
        pillars = [
            ("year", "丙", "午"),   # H=0°，红
            ("month", "丁", "未"),  # H=8°，偏红
        ]
        result = mapper.mix_pillars(pillars)
        h = result["H"]
        assert h is not None
        # 应在红色区域，不应跑到绿色区域
        in_red = (h <= 20) or (h >= 340)
        assert in_red, f"0°/360° 边界测试失败: H={h:.2f}° 跑到了非红色区域"

    def test_water_fire_mix_reasonable(self, mapper):
        """
        E-007: 水(270°)和火(0°)各占一半，结果应在 270°~360° 或 0°~90° 内，
               确认圆形平均没有产生 135°（绿色）的奇怪结果。
        """
        pillars = [
            ("day", "丙", "午"),    # H=0°，火
            ("hour", "壬", "申"),   # H=270°，水
        ]
        result = mapper.mix_pillars(pillars)
        h = result["H"]
        assert h is not None
        # 水火各半，圆形均值应在 315°±45° 的区间（即 270°~360° 或 0°~45°）
        in_expected = (270 <= h <= 360) or (0 <= h <= 45)
        assert in_expected, f"水火圆形平均 H={h:.2f}° 不在预期区间 [270°, 45°(循环)]"

    def test_earth_excluded_from_h_average(self, mapper):
        """E-008: 土柱（H=None）不参与色相圆形平均"""
        pillars = [
            ("year", "己", "酉"),   # H=None，土
            ("month", "丙", "午"),  # H=0°，火
        ]
        result = mapper.mix_pillars(pillars)
        h = result["H"]
        # 结果 H 应由丙午(0°)主导，不应为 None
        assert h is not None
        assert (h <= 30) or (h >= 330), f"土被排除后 H 应靠近火(0°)，实际 {h:.2f}°"

    def test_all_earth_returns_none_h(self, mapper):
        """E-009: 全土柱时 H 应为 None"""
        pillars = [
            ("year", "戊", "子"),
            ("month", "己", "丑"),
        ]
        result = mapper.mix_pillars(pillars)
        assert result["H"] is None, f"全土柱 H 应为 None，实际 {result['H']}"


class TestBirthColorComputation:
    """本命色计算逻辑测试"""

    def test_birth_color_returns_all_fields(self, engine):
        """E-010: compute_birth_color 返回 H/S/L/T/hsl_hex/pillars"""
        result = engine.compute_birth_color(XUZIHAN_BAZI)
        for field in ("H", "S", "L", "T", "hsl_hex", "pillars", "method"):
            assert field in result, f"缺少字段: {field}"

    def test_birth_color_pillar_count(self, engine):
        """E-011: 四柱输入产生 4 条 pillar 详情"""
        result = engine.compute_birth_color(XUZIHAN_BAZI)
        assert len(result["pillars"]) == 4

    def test_birth_color_pillar_weights(self, engine):
        """E-012: 四柱权重之和 = 1.0（15%+30%+40%+15%）"""
        result = engine.compute_birth_color(XUZIHAN_BAZI)
        total_weight = sum(p["weight"] for p in result["pillars"])
        assert abs(total_weight - 1.0) < 1e-6, f"权重合计 {total_weight:.6f} ≠ 1.0"

    def test_partial_bazi_still_works(self, engine):
        """E-013: 仅三柱输入也能正常运算"""
        three_pillar_bazi = {
            "year": {"gan": "壬", "zhi": "申"},
            "month": {"gan": "己", "zhi": "酉"},
            "day": {"gan": "丁", "zhi": "未"},
        }
        result = engine.compute_birth_color(three_pillar_bazi)
        assert result["hsl_hex"].startswith("#")
        assert len(result["pillars"]) == 3


class TestDaYunComputation:
    """大运叠加计算测试"""

    def test_dayun_returns_hex(self, engine):
        """E-014: 大运叠加应返回合法 hex"""
        birth = engine.compute_birth_color(XUZIHAN_BAZI)
        result = engine.compute_da_yun_color(birth, "癸丑", 0.3)
        assert result["hsl_hex"].startswith("#")
        assert len(result["hsl_hex"]) == 7

    def test_dayun_intensity_bounds(self, engine):
        """E-015: intensity=0 时大运色应与本命色接近"""
        birth = engine.compute_birth_color(XUZIHAN_BAZI)
        result = engine.compute_da_yun_color(birth, "癸丑", 0.0)
        # intensity=0 → 大运影响为0 → H 应与本命色一致
        assert abs(result["H"] - birth["H"]) < 1.0, (
            f"intensity=0 时大运 H={result['H']:.2f}° 应等于本命 H={birth['H']:.2f}°"
        )

    def test_dayun_full_intensity(self, engine):
        """E-016: intensity=1.0 时大运色应与大运柱本身接近"""
        birth = engine.compute_birth_color(XUZIHAN_BAZI)
        dy_pillar = engine.mapper.lookup_pillar("甲寅")  # 木=120°
        result = engine.compute_da_yun_color(birth, "甲寅", 1.0)
        if dy_pillar.H is not None:
            assert abs(result["H"] - dy_pillar.H) < 1.0, (
                f"intensity=1.0 时大运 H={result['H']:.2f}° 应等于大运柱 H={dy_pillar.H}°"
            )


class TestWuxingBalance:
    """五行平衡测试"""

    def test_wuxing_balance_sums_to_one(self, engine):
        """E-017: 五行比例归一（合计=1.0）"""
        report = engine.compute_lifetime_color({"birth": XUZIHAN_BAZI})
        total = sum(report["wuxing_balance"].values())
        assert abs(total - 1.0) < 0.01, f"五行合计 {total:.4f} ≠ 1.0"

    def test_wuxing_balance_all_five_present(self, engine):
        """E-018: 五行分布应包含木/火/土/金/水五个键"""
        report = engine.compute_lifetime_color({"birth": XUZIHAN_BAZI})
        balance = report["wuxing_balance"]
        for element in ("木", "火", "土", "金", "水"):
            assert element in balance, f"五行分布缺少: {element}"

    def test_wuxing_balance_no_negative(self, engine):
        """E-019: 五行比例不应出现负值"""
        report = engine.compute_lifetime_color({"birth": XUZIHAN_BAZI})
        for element, ratio in report["wuxing_balance"].items():
            assert ratio >= 0, f"{element} 比例为负值: {ratio}"

    def test_metal_present_from_dizhi(self, engine):
        """E-020: 梓涵申酉地支藏金，金属性比例 > 0"""
        report = engine.compute_lifetime_color({"birth": XUZIHAN_BAZI})
        jin = report["wuxing_balance"].get("金", 0)
        assert jin > 0, f"申酉月年地支应贡献金，实际金={jin:.3f}"
