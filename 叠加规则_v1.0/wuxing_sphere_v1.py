#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八字色彩 · 球体叠加引擎 + 滤色片算子实现
版本: v1.0
作者: 执中
日期: 2026-06-03

使用:
    from wuxing_sphere_v1 import WuxingSphere, WuxingOperator
    sphere = WuxingSphere()
    result_color = sphere.compute_lifetime_color(bazi_data)
"""

import math
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional


@dataclass
class HSL:
    """HSL色彩，H∈[0,360), S∈[0,1], L∈[0,1]"""
    h: float  # 色相 0-360
    s: float  # 饱和度 0-1
    l: float  # 明度 0-1

    def clamp(self) -> "HSL":
        return HSL(
            h=self.h % 360,
            s=max(0.0, min(1.0, self.s)),
            l=max(0.0, min(1.0, self.l))
        )

    def __repr__(self):
        return f"HSL(H={self.h:.1f}°, S={self.s:.2f}, L={self.l:.2f})"


class WuxingOperator:
    """
    五行滤色片算子 —— 520元清"五行=函数"模型的工程实现
    每个算子是一个变换函数: HSL × intensity → HSL
    """

    @staticmethod
    def mu(color: HSL, intensity: float) -> HSL:
        """
        木算子 · 生发（让颜色"更活"）
        低饱和时色相偏移更大，中等明度时增饱和最多
        对中性色(S<0.1)保护：饱和增量衰减
        """
        if intensity <= 0:
            return color
        i = max(0.0, min(1.0, intensity))
        sat_guard = min(1.0, color.s * 5.0)  # S=0时guard=0, S>=0.2时guard=1
        return HSL(
            h=color.h + 5.0 * i * (1 - color.s),
            s=color.s + 0.15 * i * math.sin(math.pi * color.l) * sat_guard,
            l=color.l + 0.03 * i * (0.5 - color.l)
        ).clamp()

    @staticmethod
    def huo(color: HSL, intensity: float) -> HSL:
        """
        火算子 · 炎上（让颜色"更亮"）
        高饱和时向暖偏，整体提亮（开灯效应）
        """
        if intensity <= 0:
            return color
        i = max(0.0, min(1.0, intensity))
        return HSL(
            h=color.h - 8.0 * i * color.s,
            s=color.s + 0.10 * i * color.l,
            l=color.l + 0.12 * i * (1 - color.l ** 0.5)
        ).clamp()

    @staticmethod
    def tu(color: HSL, intensity: float) -> HSL:
        """
        土算子 · 稼穑（让颜色"更稳"）
        不偏色，降饱和，向中性明度靠拢（向球心收敛）
        """
        if intensity <= 0:
            return color
        i = max(0.0, min(1.0, intensity))
        return HSL(
            h=color.h,  # 土不偏色，守中
            s=color.s - 0.20 * i * color.s,
            l=color.l - 0.05 * i * (color.l - 0.5)
        ).clamp()

    @staticmethod
    def jin(color: HSL, intensity: float) -> HSL:
        """
        金算子 · 从革（让颜色"更冷"）
        低饱和时向冷偏，微降饱和，高明度时更亮
        """
        if intensity <= 0:
            return color
        i = max(0.0, min(1.0, intensity))
        return HSL(
            h=color.h + 10.0 * i * (1 - color.s),
            s=color.s - 0.05 * i,
            l=color.l + 0.08 * i * color.l
        ).clamp()

    @staticmethod
    def shui(color: HSL, intensity: float) -> HSL:
        """
        水算子 · 润下（让颜色"更深"）
        高饱和时向蓝偏，暗部增饱和，整体压暗
        对中性色保护：压暗幅度限制
        """
        if intensity <= 0:
            return color
        i = max(0.0, min(1.0, intensity))
        # 压暗时使用sigmoid曲线：越暗压得越轻（避免死黑）
        dark_factor = color.l ** 0.5
        dark_guard = 0.5 + 0.5 * dark_factor  # L=1时guard=1, L=0时guard=0.5
        return HSL(
            h=color.h + 5.0 * i * color.s,
            s=color.s + 0.08 * i * (1 - color.l),
            l=color.l - 0.12 * i * dark_factor * dark_guard
        ).clamp()

    @classmethod
    def apply(cls, color: HSL, wuxing: str, intensity: float) -> HSL:
        """根据五行名调用对应算子"""
        operators = {
            "mu": cls.mu, "木": cls.mu, "mu": cls.mu,
            "huo": cls.huo, "火": cls.huo, "huo": cls.huo,
            "tu": cls.tu, "土": cls.tu, "tu": cls.tu,
            "jin": cls.jin, "金": cls.jin, "jin": cls.jin,
            "shui": cls.shui, "水": cls.shui, "shui": cls.shui,
        }
        op = operators.get(wuxing)
        if not op:
            raise ValueError(f"未知五行: {wuxing}")
        return op(color, intensity)

    @classmethod
    def compose(cls, color: HSL, intensities: Dict[str, float]) -> HSL:
        """
        按相生顺序复合多个五行算子: 木→火→土→金→水

        Args:
            color: 初始颜色
            intensities: {"mu": 0.1, "huo": 0.35, ...}
        """
        order = ["mu", "huo", "tu", "jin", "shui"]
        result = color
        for wx in order:
            if wx in intensities and intensities[wx] > 0:
                result = cls.apply(result, wx, intensities[wx])
        return result


class ColorMath:
    """色彩数学工具箱"""

    @staticmethod
    def hsl_to_rgb(hsl: HSL) -> Tuple[float, float, float]:
        """HSL → RGB (0~1)"""
        h, s, l = hsl.h / 360.0, hsl.s, hsl.l
        if s == 0:
            return (l, l, l)

        def hue_to_rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p

        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)
        return (r, g, b)

    @staticmethod
    def rgb_to_hsl(r: float, g: float, b: float) -> HSL:
        """RGB (0~1) → HSL"""
        mx, mn = max(r, g, b), min(r, g, b)
        l = (mx + mn) / 2

        if mx == mn:
            return HSL(0, 0, l)

        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)

        if mx == r:
            h = ((g - b) / d + (6 if g < b else 0)) * 60
        elif mx == g:
            h = ((b - r) / d + 2) * 60
        else:
            h = ((r - g) / d + 4) * 60

        return HSL(h, s, l)

    @staticmethod
    def blend_overlay(base_rgb: Tuple[float, ...], blend_rgb: Tuple[float, ...]) -> Tuple[float, ...]:
        """Overlay混合（Photoshop标准公式）"""
        result = []
        for b, l in zip(base_rgb, blend_rgb):
            if b < 0.5:
                result.append(2 * b * l)
            else:
                result.append(1 - 2 * (1 - b) * (1 - l))
        return tuple(max(0, min(1, c)) for c in result)

    @staticmethod
    def cubic_weighted_blend(colors: List[Tuple[float, ...]], weights: List[float]) -> Tuple[float, ...]:
        """
        带权重的高次混合 —— 避免灰色泥沼
        平方加权让主导色更鲜明
        """
        assert abs(sum(weights) - 1.0) < 0.01, f"权重和必须为1，当前={sum(weights)}"
        assert len(colors) == len(weights)

        # 权重幂次化：削弱小权重的稀释作用
        powers = [w ** 0.7 for w in weights]
        sum_powers = sum(powers)
        normalized = [p / sum_powers for p in powers]

        # 分量级平方加权
        result = [0.0, 0.0, 0.0]
        for rgb, w in zip(colors, normalized):
            for i in range(3):
                result[i] += (rgb[i] ** 2) * w

        # 还原并截断
        result = [max(0, min(1, math.sqrt(c))) for c in result]
        return tuple(result)

    @staticmethod
    def rgb_to_hex(rgb: Tuple[float, ...]) -> str:
        """RGB转十六进制颜色"""
        return "#" + "".join(f"{int(max(0,min(1,c))*255):02X}" for c in rgb)


class WuxingSphere:
    """
    八字色彩球体叠加引擎
    整合：柱内叠加(司辰规则) + 滤色片算子(520元清) + 三层球体(梓涵理论)
    """

    def __init__(self):
        self.op = WuxingOperator()
        self.math = ColorMath()

        # 命局四柱权重（日柱为核心）
        self.pillar_weights = {
            "year": 0.15,
            "month": 0.25,
            "day": 0.40,
            "hour": 0.20
        }

        # 柱内层级透明度（司辰5/30定稿）
        self.layer_opacity = {
            "ganzhi": 1.00,   # 干支层：100%
            "shensha": 0.50,  # 神煞层：50%（取中间值）
            "canggan": 0.22   # 藏干层：22%（取中间值）
        }

    # ═══════════════════════════════════════════════════════
    # 第一层：柱内叠加（单柱合成）
    # ═══════════════════════════════════════════════════════

    def compute_pillar_color(
        self,
        gan_wuxing: str,
        zhi_wuxing: str,
        gan_weight: float = 0.5,
        zhi_weight: float = 0.5,
        shensha_list: Optional[List[Dict]] = None,
        canggan_list: Optional[List[Dict]] = None
    ) -> HSL:
        """
        计算单柱颜色（柱内叠加）

        Args:
            gan_wuxing: 天干五行 (mu/huo/tu/jin/shui)
            zhi_wuxing: 地支五行
            gan_weight: 干权重
            zhi_weight: 支权重
            shensha_list: [{"wuxing": "火", "intensity": 0.5, "priority": 1}, ...]
            canggan_list: [{"wuxing": "木", "intensity": 0.3}, ...]

        Returns:
            该柱的HSL颜色
        """
        shensha_list = shensha_list or []
        canggan_list = canggan_list or []

        # Step 1: 干支层底色（用五行算子从纯灰生成基准色）
        # 天干色：从球面纯色调入
        gan_color = self._wuxing_base_color(gan_wuxing, gan_weight)
        zhi_color = self._wuxing_base_color(zhi_wuxing, zhi_weight)

        # 干支Overlay混合
        ganzhi_rgb = self.math.blend_overlay(
            self.math.hsl_to_rgb(gan_color),
            self.math.hsl_to_rgb(zhi_color)
        )
        ganzhi_hsl = self.math.rgb_to_hsl(*ganzhi_rgb)

        # Step 2: 神煞层叠色（按优先级排序，Alpha混合）
        shensha_hsl = ganzhi_hsl
        sorted_shensha = sorted(shensha_list, key=lambda x: x.get("priority", 99))
        for ss in sorted_shensha:
            ss_color = self._wuxing_base_color(ss["wuxing"], ss.get("intensity", 0.3))
            opacity = ss.get("opacity", self.layer_opacity["shensha"])
            # Alpha混合
            ss_rgb = self.math.hsl_to_rgb(ss_color)
            base_rgb = self.math.hsl_to_rgb(shensha_hsl)
            blended = tuple(
                base_rgb[i] * (1 - opacity) + ss_rgb[i] * opacity
                for i in range(3)
            )
            shensha_hsl = self.math.rgb_to_hsl(*blended)

        # Step 3: 藏干层纹理（低透明度Alpha混合）
        final_hsl = shensha_hsl
        for cg in canggan_list:
            cg_color = self._wuxing_base_color(cg["wuxing"], cg.get("intensity", 0.2))
            opacity = cg.get("opacity", self.layer_opacity["canggan"])
            cg_rgb = self.math.hsl_to_rgb(cg_color)
            base_rgb = self.math.hsl_to_rgb(final_hsl)
            blended = tuple(
                base_rgb[i] * (1 - opacity) + cg_rgb[i] * opacity
                for i in range(3)
            )
            final_hsl = self.math.rgb_to_hsl(*blended)

        return final_hsl.clamp()

    def _wuxing_base_color(self, wuxing: str, intensity: float = 1.0) -> HSL:
        """
        生成五行基准色（球面纯色区中心点）
        这是每个五行的"本色"，位于球面（S=1, L=0.5）
        """
        # 五行扇区中心角度（暂定，待梓涵确认）
        centers = {
            "mu": 105.0,    # 木：翠绿
            "huo": 195.0,   # 火：正红（在HSL中0°=红，但火扇区中心设为195是为了... 等等，这里有问题）
            "tu": 45.0,     # 土：暖黄
            "jin": 285.0,   # 金：银白偏冷
            "shui": 345.0,  # 水：深海蓝
        }
        # 中文别名
        aliases = {"木": "mu", "火": "huo", "土": "tu", "金": "jin", "水": "shui"}
        wx = aliases.get(wuxing, wuxing)

        center_h = centers.get(wx, 0)
        # 根据intensity微调：强度越高越接近中心色，越低越向灰偏
        s = 0.5 + 0.5 * intensity  # intensity=1 → S=1（纯），intensity=0 → S=0.5（半灰）
        l = 0.5  # 球面基准明度

        return HSL(h=center_h, s=s, l=l)

    # ═══════════════════════════════════════════════════════
    # 第二层：四柱合并（本命球体）
    # ═══════════════════════════════════════════════════════

    def compute_birth_color(
        self,
        pillars: Dict[str, Dict]
    ) -> HSL:
        """
        合并四柱颜色 → 本命基准色

        Args:
            pillars: {
                "year": {"gan_wuxing": "水", "zhi_wuxing": "金", ...},
                "month": {...},
                "day": {...},
                "hour": {...}
            }
        """
        pillar_colors = {}
        for name, data in pillars.items():
            pillar_colors[name] = self.compute_pillar_color(**data)

        # 用cubic混合合并四柱
        rgb_list = [self.math.hsl_to_rgb(pillar_colors[p]) for p in ["year", "month", "day", "hour"]]
        weights = [self.pillar_weights[p] for p in ["year", "month", "day", "hour"]]

        merged_rgb = self.math.cubic_weighted_blend(rgb_list, weights)
        return self.math.rgb_to_hsl(*merged_rgb)

    # ═══════════════════════════════════════════════════════
    # 第三层：大运/流年叠加（滤色片算子复合）
    # ═══════════════════════════════════════════════════════

    def compute_da_yun_transform(self, da_yun_wuxing: Dict[str, float]) -> "Transform":
        """
        生成大运变换函数
        输入: {"shui": 0.6, "tu": 0.4}
        输出: 可调用变换函数
        """
        return Transform(self.op, da_yun_wuxing)

    def compute_liu_nian_transform(self, liu_nian_wuxing: Dict[str, float]) -> "Transform":
        """生成流年变换函数"""
        return Transform(self.op, liu_nian_wuxing)

    def apply_lifetime_overlay(
        self,
        birth_color: HSL,
        da_yun_wuxing: Dict[str, float],
        liu_nian_wuxing: Dict[str, float]
    ) -> HSL:
        """
        三层叠加: 本命 → 大运 → 流年
        C = T_流年( T_大运( 本命色 ) )
        """
        # 大运变换
        dy = self.compute_da_yun_transform(da_yun_wuxing)
        after_da_yun = dy.apply(birth_color)

        # 流年变换
        ln = self.compute_liu_nian_transform(liu_nian_wuxing)
        final = ln.apply(after_da_yun)

        return final.clamp()

    # ═══════════════════════════════════════════════════════
    # 端到端计算
    # ═══════════════════════════════════════════════════════

    def compute_lifetime_color(
        self,
        bazi_data: Dict
    ) -> Dict:
        """
        端到端计算：从八字数据到最终颜色

        Args:
            bazi_data: {
                "pillars": {年/月/日/柱数据},
                "da_yun": {"shui": 0.6, "tu": 0.4},
                "liu_nian": {"mu": 0.4, "huo": 0.6}
            }

        Returns:
            {
                "birth_color": HSL,
                "after_da_yun": HSL,
                "final_color": HSL,
                "hex": "#RRGGBB",
                "layer_report": {...}
            }
        """
        # 本命色
        birth = self.compute_birth_color(bazi_data["pillars"])

        # 大运
        dy_transform = self.compute_da_yun_transform(bazi_data.get("da_yun", {}))
        after_dy = dy_transform.apply(birth)

        # 流年
        ln_transform = self.compute_liu_nian_transform(bazi_data.get("liu_nian", {}))
        final = ln_transform.apply(after_dy)

        # 导出报告
        return {
            "birth_color": birth,
            "after_da_yun": after_dy,
            "final_color": final,
            "hex": self.math.rgb_to_hex(self.math.hsl_to_rgb(final)),
            "layer_report": {
                "birth_hex": self.math.rgb_to_hex(self.math.hsl_to_rgb(birth)),
                "da_yun_hex": self.math.rgb_to_hex(self.math.hsl_to_rgb(after_dy)),
                "final_hex": self.math.rgb_to_hex(self.math.hsl_to_rgb(final)),
            }
        }


class Transform:
    """可复用的滤色片变换函数"""

    def __init__(self, operator: WuxingOperator, intensities: Dict[str, float]):
        self.op = operator
        self.intensities = intensities

    def apply(self, color: HSL) -> HSL:
        return self.op.compose(color, self.intensities)


# ═══════════════════════════════════════════════════════
# 自检模块
# ═══════════════════════════════════════════════════════

class SelfCheck:
    """数学自检（规格7.1节）"""

    def __init__(self):
        self.op = WuxingOperator()
        self.passed = 0
        self.failed = 0

    def check(self, name: str, condition: bool, detail: str = ""):
        if condition:
            self.passed += 1
            print(f"  [OK] {name}")
        else:
            self.failed += 1
            print(f"  [FAIL] {name}: {detail}")

    def run_all(self):
        print("\n=== 滤色片算子自检 ===")

        # 1. 算子封闭性
        test_color = HSL(120, 0.5, 0.5)
        for wx in ["mu", "huo", "tu", "jin", "shui"]:
            result = self.op.apply(test_color, wx, 1.0)
            valid = (0 <= result.h < 360) and (0 <= result.s <= 1) and (0 <= result.l <= 1)
            self.check(f"封闭性 [{wx}]", valid, f"H={result.h}, S={result.s}, L={result.l}")

        # 2. 土算子幂等性（近似）
        gray = HSL(0, 0.5, 0.5)
        t1 = self.op.tu(gray, 0.5)
        t2 = self.op.tu(t1, 0.5)
        t_combined = self.op.tu(gray, 1.0)
        diff = abs(t2.s - t_combined.s) + abs(t2.l - t_combined.l)
        self.check("土算子幂等性", diff < 0.05, f"diff={diff:.4f}")

        # 3. 中性色稳定性
        neutral = HSL(120, 0, 0.5)
        for wx in ["mu", "huo", "tu", "jin", "shui"]:
            result = self.op.apply(neutral, wx, 1.0)
            stable = abs(result.l - 0.5) < 0.1 and result.s < 0.15
            self.check(f"中性色稳定性 [{wx}]", stable)

        # 4. 叠加单调性
        c1 = self.op.mu(test_color, 0.3)
        c2 = self.op.mu(test_color, 0.6)
        # 强度增大，饱和度应不减（木算子增饱和）
        self.check("叠加单调性", c2.s >= c1.s - 0.01)

        # 5. 五行和约束
        weights = {"mu": 0.1, "huo": 0.35, "tu": 0.2, "shui": 0.2, "jin": 0.15}
        total = sum(weights.values())
        self.check("五行和约束", 0.8 <= total <= 1.2, f"sum={total}")

        print(f"\n结果: {self.passed} 通过, {self.failed} 失败")
        return self.failed == 0


# ═══════════════════════════════════════════════════════
# 演示 / 测试
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("八字色彩 · 球体叠加引擎 v1.0")
    print("=" * 60)

    # 运行自检
    checker = SelfCheck()
    checker.run_all()

    print("\n" + "=" * 60)
    print("演示: 梓涵八字色彩计算（简化版）")
    print("=" * 60)

    sphere = WuxingSphere()

    # 梓涵八字简化数据
    zihan_bazi = {
        "pillars": {
            "year": {
                "gan_wuxing": "水", "zhi_wuxing": "金",
                "gan_weight": 0.5, "zhi_weight": 0.5,
                "shensha_list": [],
                "canggan_list": [
                    {"wuxing": "金", "intensity": 0.3},
                    {"wuxing": "水", "intensity": 0.2}
                ]
            },
            "month": {
                "gan_wuxing": "土", "zhi_wuxing": "金",
                "gan_weight": 0.35, "zhi_weight": 0.65,
                "shensha_list": [
                    {"wuxing": "金", "intensity": 0.5, "priority": 1, "name": "天乙"},
                    {"wuxing": "火", "intensity": 0.3, "priority": 4, "name": "桃花"}
                ],
                "canggan_list": [{"wuxing": "金", "intensity": 0.25}]
            },
            "day": {
                "gan_wuxing": "火", "zhi_wuxing": "土",
                "gan_weight": 0.45, "zhi_weight": 0.55,
                "shensha_list": [],
                "canggan_list": [
                    {"wuxing": "土", "intensity": 0.2},
                    {"wuxing": "火", "intensity": 0.15},
                    {"wuxing": "木", "intensity": 0.1}
                ]
            },
            "hour": {
                "gan_wuxing": "火", "zhi_wuxing": "火",
                "gan_weight": 0.55, "zhi_weight": 0.45,
                "shensha_list": [{"wuxing": "火", "intensity": 0.4, "priority": 2, "name": "将星"}],
                "canggan_list": [
                    {"wuxing": "火", "intensity": 0.2},
                    {"wuxing": "土", "intensity": 0.15}
                ]
            }
        },
        "da_yun": {"水": 0.6, "土": 0.4},   # 癸丑大运
        "liu_nian": {"木": 0.4, "火": 0.6}   # 乙巳流年
    }

    result = sphere.compute_lifetime_color(zihan_bazi)

    print(f"\n本命基准色:    {result['birth_color']} → {result['layer_report']['birth_hex']}")
    print(f"大运叠加后:    {result['after_da_yun']} → {result['layer_report']['da_yun_hex']}")
    print(f"流年叠加后:    {result['final_color']} → {result['layer_report']['final_hex']}")
    print(f"\n最终推荐色: {result['hex']}")

    print("\n" + "=" * 60)
    print("五行算子效果演示（从纯灰出发）")
    print("=" * 60)
    gray = HSL(0, 0, 0.5)
    for wx_name, wx_key in [("木", "mu"), ("火", "huo"), ("土", "tu"), ("金", "jin"), ("水", "shui")]:
        result_hsl = sphere.op.apply(gray, wx_key, 1.0)
        result_rgb = sphere.math.hsl_to_rgb(result_hsl)
        hex_val = sphere.math.rgb_to_hex(result_rgb)
        print(f"  {wx_name}算子(灰): {result_hsl} → {hex_val}")
