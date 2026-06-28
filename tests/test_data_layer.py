"""
数据层测试 — JSON 映射表 & 查表功能
"""
import json
import os

import pytest


# ─── JSON 数据完整性 ────────────────────────────────────────────

class TestJsonIntegrity:
    """ganzhi_sphere_map_v1.3.json 数据完整性测试"""

    JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "ganzhi_sphere_map_v1.3.json")

    @pytest.fixture(scope="class")
    def raw_data(self):
        with open(self.JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_json_loads(self, raw_data):
        """D-001: JSON 文件能正常加载"""
        assert raw_data is not None

    def test_records_count(self, raw_data):
        """D-002: 六十甲子正好 60 条"""
        assert len(raw_data["records"]) == 60, (
            f"期望 60 条，实际 {len(raw_data['records'])} 条"
        )

    def test_records_required_fields(self, raw_data):
        """D-003: 每条 record 必须有 ganzhi/tiangan/dizhi/wuxing/S/L/T/stage/wangshuai"""
        required = {"ganzhi", "tiangan", "dizhi", "wuxing", "S", "L", "T", "stage", "wangshuai"}
        for rec in raw_data["records"]:
            missing = required - set(rec.keys())
            assert not missing, f"{rec['ganzhi']} 缺少字段: {missing}"

    def test_records_no_duplicate_ganzhi(self, raw_data):
        """D-004: 六十甲子无重复"""
        ganzhi_list = [r["ganzhi"] for r in raw_data["records"]]
        duplicates = [gz for gz in ganzhi_list if ganzhi_list.count(gz) > 1]
        assert not duplicates, f"重复干支: {set(duplicates)}"

    def test_hsl_value_ranges(self, raw_data):
        """D-005: H/S/L 在有效范围内"""
        for rec in raw_data["records"]:
            gz = rec["ganzhi"]
            h = rec.get("H")
            s = rec["S"]
            l_val = rec["L"]
            if h is not None:
                assert 0 <= h < 360, f"{gz}: H={h} 超出 [0, 360)"
            assert 0 <= s <= 1, f"{gz}: S={s} 超出 [0, 1]"
            assert 0 <= l_val <= 1, f"{gz}: L={l_val} 超出 [0, 1]"

    def test_color_temperature_range(self, raw_data):
        """D-006: 色温 T 在合理范围 [1500K, 15000K]"""
        for rec in raw_data["records"]:
            t = rec["T"]
            assert 1500 <= t <= 15000, (
                f"{rec['ganzhi']}: T={t}K 超出合理范围 [1500K, 15000K]"
            )

    def test_earth_pillar_h_is_null(self, raw_data):
        """D-007: 土属性（戊/己）天干的 H 值应为 null"""
        earth_gan = {"戊", "己"}
        for rec in raw_data["records"]:
            if rec["tiangan"] in earth_gan:
                assert rec.get("H") is None, (
                    f"{rec['ganzhi']}: 土天干 H 应为 null，实际 {rec.get('H')}"
                )

    def test_fire_pillars_h_in_red_zone(self, raw_data):
        """D-008: 火属性（丙/丁）天干的 H 值应在红色区（0°±30°）"""
        fire_gan = {"丙", "丁"}
        for rec in raw_data["records"]:
            if rec["tiangan"] in fire_gan:
                h = rec.get("H")
                assert h is not None, f"{rec['ganzhi']}: 火天干 H 不应为 null"
                in_red = (h <= 30) or (h >= 330)
                assert in_red, (
                    f"{rec['ganzhi']}: 火天干 H={h}° 应在红色区（<=30° 或 >=330°）"
                )

    def test_water_pillars_h_in_blue_zone(self, raw_data):
        """D-009: 水属性（壬/癸）天干的 H 值应在蓝紫区（240°±40°）"""
        water_gan = {"壬", "癸"}
        for rec in raw_data["records"]:
            if rec["tiangan"] in water_gan:
                h = rec.get("H")
                assert h is not None, f"{rec['ganzhi']}: 水天干 H 不应为 null"
                assert 200 <= h <= 290, (
                    f"{rec['ganzhi']}: 水天干 H={h}° 应在蓝紫区 [200°, 290°]"
                )


# ─── 查表功能 ───────────────────────────────────────────────────

class TestPillarLookup:
    """SichenPillarMapper 查表功能测试"""

    def test_lookup_bingwu(self, mapper, engine_module):
        """D-010: 丙午查表 H=0°(纯红/火旺)"""
        pc = mapper.lookup_pillar("丙午")
        assert pc.H == 0, f"丙午 H 应为 0°，实际 {pc.H}"
        assert pc.wuxing == "火"

    def test_lookup_renxu(self, mapper):
        """D-011: 壬申查表 H=270°(水/蓝紫)"""
        pc = mapper.lookup_pillar("壬申")
        assert pc.H == 270, f"壬申 H 应为 270°，实际 {pc.H}"

    def test_lookup_jiayou_earth(self, mapper):
        """D-012: 己酉查表 H=None(土天干)"""
        pc = mapper.lookup_pillar("己酉")
        assert pc.H is None, f"己酉 H 应为 None，实际 {pc.H}"
        assert pc.wuxing in ("土", "金"), f"己酉五行标注: {pc.wuxing}"

    def test_lookup_invalid_raises(self, mapper):
        """D-013: 查不存在的干支应抛 ValueError"""
        with pytest.raises(ValueError, match="未知干支"):
            mapper.lookup_pillar("甲甲")

    def test_lookup_gan_zhi_api(self, mapper):
        """D-014: lookup_gan_zhi 与 lookup_pillar 结果一致"""
        by_gz = mapper.lookup_pillar("甲子")
        by_gan_zhi = mapper.lookup_gan_zhi("甲", "子")
        assert by_gz.H == by_gan_zhi.H
        assert by_gz.S == by_gan_zhi.S
        assert by_gz.L == by_gan_zhi.L

    def test_all_60_pillars_loadable(self, mapper):
        """D-015: 六十甲子全部可以正常查表"""
        SIXTY_JIAZI = [
            "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
            "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
            "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
            "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
            "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
            "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥",
        ]
        for gz in SIXTY_JIAZI:
            try:
                pc = mapper.lookup_pillar(gz)
                assert pc.ganzhi == gz
            except Exception as e:
                pytest.fail(f"查 {gz} 失败: {e}")
