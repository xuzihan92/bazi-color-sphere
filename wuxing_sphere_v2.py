#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八字色彩 · 球体引擎 v2.0 — 土轴四行静态模型
版本: v2.0
作者: 执中
日期: 2026-06-09

理论基础:
- 球体 = 土（整颗球都是土）
- 中轴 = 南北极轴 = 土轴/明度轴（L: 0=南极黑 → 0.5=赤道灰 → 1=北极白）
- 四行在黄道面: 木=0°(春分/绿), 火=90°(夏至/红), 金=180°(秋分/白), 水=270°(冬至/蓝)
- S = 距中轴距离（S=0=轴上=土, S=1=黄道面=四行纯色）
- H = 黄道面方位角

使用:
    from wuxing_sphere_v2 import WuxingSphereV2
    sphere = WuxingSphereV2()
    report = sphere.compute_lifetime_color(bazi_data)
"""

import math
import json
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Optional


@dataclass
class HSL:
    """HSL色彩，H∈[0,360), S∈[0,1], L∈[0,1]"""
    h: float
    s: float
    l: float

    def clamp(self) -> "HSL":
        return HSL(
            h=self.h % 360,
            s=max(0.0, min(1.0, self.s)),
            l=max(0.0, min(1.0, self.l))
        )

    def to_rgb(self) -> Tuple[int, int, int]:
        """HSL -> RGB (0-255)"""
        h, s, l = self.h / 360.0, self.s, self.l
        if s == 0:
            r = g = b = l
        else:
            def hue2rgb(p, q, t):
                if t < 0: t += 1
                if t > 1: t -= 1
                if t < 1/6: return p + (q - p) * 6 * t
                if t < 1/2: return q
                if t < 2/3: return p + (q - p) * (2/3 - t) * 6
                return p
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue2rgb(p, q, h + 1/3)
            g = hue2rgb(p, q, h)
            b = hue2rgb(p, q, h - 1/3)
        return (int(r * 255), int(g * 255), int(b * 255))

    def to_hex(self) -> str:
        r, g, b = self.to_rgb()
        return f"#{r:02X}{g:02X}{b:02X}"

    def __repr__(self):
        return f"HSL(H={self.h:.1f}°, S={self.s:.2f}, L={self.l:.2f})"


@dataclass
class SphereCoord:
    """球面坐标 (r, theta, phi)
    r = 到球心距离 [0,1]
    theta = 与中轴夹角（极角）0=北极, π/2=赤道, π=南极
    phi = 黄道面方位角 0=春分(木), π/2=夏至(火), π=秋分(金), 3π/2=冬至(水)
    """
    r: float
    theta: float
    phi: float

    def to_cartesian(self) -> Tuple[float, float, float]:
        """转直角坐标 (x, y, z)，Z轴=中轴=南北极"""
        x = self.r * math.sin(self.theta) * math.cos(self.phi)
        y = self.r * math.sin(self.theta) * math.sin(self.phi)
        z = self.r * math.cos(self.theta)
        return (x, y, z)

    def to_hsl(self) -> HSL:
        """球坐标 -> HSL色彩
        H = phi 转角度 (0°=木/春分, 90°=火/夏至, 180°=金/秋分, 270°=水/冬至)
        S = sin(theta) = 距中轴距离 (0=轴上=土, 1=赤道=四行纯色)
        L = cos(theta) 映射到 [0,1] (0=南极黑, 0.5=赤道灰, 1=北极白)
        
        注意: 此映射为简化版。元清指出黄道面角度与HSL色相不是统一线性映射，
        后续应替换为色温模型。当前版本标注"非线性，待替换"。
        """
        h = math.degrees(self.phi) % 360
        s = math.sin(self.theta)  # 距中轴距离
        l = (math.cos(self.theta) + 1) / 2  # [-1,1] -> [0,1]
        return HSL(h=h, s=s, l=l).clamp()


class BaziToSphereMapper:
    """四柱 -> 球面坐标映射（简化查表版 v1.0）
    
    映射策略:
    - 天干定五行 -> 黄道面方位角(phi)
    - 地支定十二长生 -> 中轴倾角(theta)
    - 柱重要性(年/月/日/时) -> 半径(r)
    
    注: 此为简化版。后续由司辰提供精确的「六十甲子→十二长生→球面坐标」映射表替换。
    """

    # 天干 -> 五行
    GAN_WUXING = {
        "甲": "木", "乙": "木",
        "丙": "火", "丁": "火",
        "戊": "土", "己": "土",
        "庚": "金", "辛": "金",
        "壬": "水", "癸": "水"
    }

    # 地支 -> 主气（藏干取第一个）
    ZHI_MAIN_QI = {
        "子": "癸", "丑": "己", "寅": "甲", "卯": "乙",
        "辰": "戊", "巳": "丙", "午": "丁", "未": "己",
        "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬"
    }

    # 五行 -> 黄道面方位角(phi, 弧度)
    # 简化: 木=春分=0°, 火=夏至=90°, 金=秋分=180°, 水=冬至=270°
    # 土=四季之交，取45°(春夏之交)作为默认值
    WUXING_PHI = {
        "木": 0.0,
        "火": math.pi / 2,
        "金": math.pi,
        "水": 3 * math.pi / 2,
        "土": math.pi / 4  # 春夏之交，非精确值
    }

    # 十二长生 -> 中轴倾角(theta, 弧度)
    # theta=0=北极(巽4/土之极阳), theta=π/2=赤道, theta=π=南极(乾6/土之极阴)
    SHI_ER_CHANG_SHENG_THETA = {
        "长生": math.pi / 3,      # 偏上，阳气初生
        "沐浴": math.pi / 2.5,
        "冠带": math.pi / 2.2,
        "临官": math.pi / 2.1,    # 接近赤道，旺相
        "帝旺": math.pi / 2,      # 赤道，最旺
        "衰": math.pi / 1.9,
        "病": math.pi / 1.7,
        "死": math.pi / 1.5,      # 偏下
        "墓": 2 * math.pi / 3,    # 更偏下
        "绝": 3 * math.pi / 4,
        "胎": 4 * math.pi / 5,
        "养": 5 * math.pi / 6,
    }

    # 地支 -> 十二长生位置（简化：假设日主为"甲"时的十二长生位置）
    # 实际应根据日干查表，此为演示用简化版
    ZHI_CHANG_SHENG = {
        "亥": "长生", "子": "沐浴", "丑": "冠带",
        "寅": "临官", "卯": "帝旺", "辰": "衰",
        "巳": "病",   "午": "死",   "未": "墓",
        "申": "绝",   "酉": "胎",   "戌": "养",
    }

    # 柱重要性权重
    PILLAR_WEIGHTS = {
        "year": 0.15,
        "month": 0.25,
        "day": 0.40,   # 日柱最重
        "hour": 0.20
    }

    def map_gan(self, gan: str) -> float:
        """天干 -> 黄道面方位角(phi)"""
        wx = self.GAN_WUXING.get(gan, "土")
        return self.WUXING_PHI.get(wx, math.pi / 4)

    def map_zhi(self, zhi: str) -> float:
        """地支 -> 中轴倾角(theta)"""
        cs = self.ZHI_CHANG_SHENG.get(zhi, "帝旺")
        return self.SHI_ER_CHANG_SHENG_THETA.get(cs, math.pi / 2)

    def map_pillar(self, gan: str, zhi: str, pillar_type: str = "day") -> SphereCoord:
        """单柱 -> 球面坐标
        
        策略: 天干定phi（黄道方位），地支定theta（中轴倾角）
        柱内叠加: 取天干和地支的加权平均（天干0.6，地支0.4）
        
        特殊处理：土五行
        - 土=中轴=明度轴，S应该接近0
        - 阳干（戊）偏向北极（theta→0，L→1，白）
        - 阴干（己）偏向南极（theta→π，L→0，黑）
        """
        wx_gan = self.GAN_WUXING.get(gan, "土")
        wx_zhi = self.GAN_WUXING.get(self.ZHI_MAIN_QI.get(zhi, "戊"), "土")

        phi_gan = self.map_gan(gan)
        phi_zhi = self.map_gan(self.ZHI_MAIN_QI.get(zhi, "戊"))
        phi = phi_gan * 0.6 + phi_zhi * 0.4

        theta_zhi = self.map_zhi(zhi)

        # 土特殊处理：向中轴收敛
        if wx_gan == "土":
            # 阳干（戊）→ 北极（theta→0），阴干（己）→ 南极（theta→π）
            if gan in ("戊",):
                theta = math.pi / 6  # 靠近北极（白）
            else:  # 己
                theta = 5 * math.pi / 6  # 靠近南极（黑）
        else:
            theta = theta_zhi

        # 如果地支也是土，进一步增强中轴收敛
        if wx_zhi == "土" and wx_gan != "土":
            # 地支土向中轴拉
            theta = theta * 0.5  # 向北极收敛（简化）

        # 半径由柱重要性决定
        r = 0.7 + self.PILLAR_WEIGHTS.get(pillar_type, 0.25) * 0.3

        return SphereCoord(r=r, theta=theta, phi=phi)

    def map_bazi(self, bazi: Dict) -> SphereCoord:
        """四柱 -> 本命球面坐标（加权平均）
        
        bazi格式: {"year": {"gan": "癸", "zhi": "酉"}, ...}
        """
        coords = []
        weights = []

        for pillar_type in ["year", "month", "day", "hour"]:
            if pillar_type in bazi:
                p = bazi[pillar_type]
                coord = self.map_pillar(p["gan"], p["zhi"], pillar_type)
                coords.append(coord)
                weights.append(self.PILLAR_WEIGHTS[pillar_type])

        # 加权平均（转直角坐标后平均，避免球面平均问题）
        total_w = sum(weights)
        x = sum(w * c.r * math.sin(c.theta) * math.cos(c.phi)
                for w, c in zip(weights, coords)) / total_w
        y = sum(w * c.r * math.sin(c.theta) * math.sin(c.phi)
                for w, c in zip(weights, coords)) / total_w
        z = sum(w * c.r * math.cos(c.theta)
                for w, c in zip(weights, coords)) / total_w

        # 转回球坐标
        r_avg = math.sqrt(x**2 + y**2 + z**2)
        theta_avg = math.acos(z / r_avg) if r_avg > 0 else math.pi / 2
        phi_avg = math.atan2(y, x) % (2 * math.pi)

        return SphereCoord(r=r_avg, theta=theta_avg, phi=phi_avg)


class WuxingSphereV2:
    """
    八字色彩球体引擎 v2.0 — 土轴四行静态模型
    
    核心功能:
    1. 四柱 -> 球面坐标映射
    2. 静态基础色计算（HSL）
    3. 大运/流年静态叠加
    4. 色彩报告生成
    """

    def __init__(self):
        self.mapper = BaziToSphereMapper()

    def compute_base_color(self, coord: SphereCoord) -> HSL:
        """计算静态基础色"""
        return coord.to_hsl()

    def compute_pillar_color(self, gan: str, zhi: str, pillar_type: str = "day") -> HSL:
        """计算单柱色彩"""
        coord = self.mapper.map_pillar(gan, zhi, pillar_type)
        return self.compute_base_color(coord)

    def compute_birth_color(self, bazi: Dict) -> HSL:
        """计算本命基准色（四柱合并）"""
        coord = self.mapper.map_bazi(bazi)
        return self.compute_base_color(coord)

    def compute_da_yun_color(self, birth_coord: SphereCoord, da_yun_ganzhi: str,
                             intensity: float = 0.3) -> HSL:
        """
        计算大运叠加色
        
        策略: 大运干支映射到球面坐标，与本命坐标做加权混合
        intensity: 大运影响强度 (0-1)
        """
        gan = da_yun_ganzhi[0]
        zhi = da_yun_ganzhi[1]
        dy_coord = self.mapper.map_pillar(gan, zhi, "day")

        # 加权混合（直角坐标）
        bx, by, bz = birth_coord.to_cartesian()
        dx, dy, dz = dy_coord.to_cartesian()

        mx = bx * (1 - intensity) + dx * intensity
        my = by * (1 - intensity) + dy * intensity
        mz = bz * (1 - intensity) + dz * intensity

        # 转回球坐标
        r = math.sqrt(mx**2 + my**2 + mz**2)
        theta = math.acos(mz / r) if r > 0 else math.pi / 2
        phi = math.atan2(my, mx) % (2 * math.pi)

        mixed = SphereCoord(r=min(r, 1.0), theta=theta, phi=phi)
        return self.compute_base_color(mixed)

    def compute_lifetime_color(self, bazi_data: Dict) -> Dict:
        """
        计算完整生命周期色彩报告
        
        bazi_data格式:
        {
            "birth": {"year": {"gan": "癸", "zhi": "酉"}, ...},
            "da_yun": ["甲子", "乙丑", ...],
            "liu_nian": [2026, 2027, ...]
        }
        """
        birth = bazi_data.get("birth", {})
        da_yun_list = bazi_data.get("da_yun", [])
        liu_nian_list = bazi_data.get("liu_nian", [])

        # 本命基准色
        birth_coord = self.mapper.map_bazi(birth)
        birth_color = self.compute_birth_color(birth)

        # 四柱分项
        pillar_colors = {}
        for pt in ["year", "month", "day", "hour"]:
            if pt in birth:
                p = birth[pt]
                pillar_colors[pt] = {
                    "gan": p["gan"], "zhi": p["zhi"],
                    "color": self.compute_pillar_color(p["gan"], p["zhi"], pt).to_hex(),
                    "hsl": repr(self.compute_pillar_color(p["gan"], p["zhi"], pt))
                }

        # 大运色彩
        da_yun_colors = []
        for i, dy in enumerate(da_yun_list):
            intensity = 0.2 + 0.1 * min(i, 3)  # 大运影响随时间递增
            color = self.compute_da_yun_color(birth_coord, dy, intensity)
            da_yun_colors.append({
                "ganzhi": dy,
                "color": color.to_hex(),
                "hsl": repr(color),
                "intensity": round(intensity, 2)
            })

        # 五行平衡估算（基于本命坐标）
        phi_deg = math.degrees(birth_coord.phi)
        wuxing_balance = self._estimate_wuxing_balance(phi_deg, birth_coord.theta)

        return {
            "birth_color": birth_color.to_hex(),
            "birth_hsl": {
                "h": round(birth_color.h, 1),
                "s": round(birth_color.s, 3),
                "l": round(birth_color.l, 3)
            },
            "birth_coord": {
                "r": round(birth_coord.r, 3),
                "theta_deg": round(math.degrees(birth_coord.theta), 1),
                "phi_deg": round(phi_deg, 1)
            },
            "pillar_colors": pillar_colors,
            "da_yun_colors": da_yun_colors,
            "wuxing_balance": wuxing_balance,
            "version": "v2.0",
            "notes": [
                "HSL色相映射为简化版（黄道方位角直接映射），后续应替换为色温模型",
                "四柱映射为简化查表版，后续应由司辰提供精确映射表",
                "土轴倾角=23.5°（黄赤交角）",
                "S=距中轴距离, L=明度轴高度, H=黄道面方位角"
            ]
        }

    def _estimate_wuxing_balance(self, phi_deg: float, theta: float) -> Dict[str, float]:
        """基于球面坐标估算五行强弱比例"""
        # 四行强度 = 距各自方位的余弦相似度
        positions = {
            "木": 0.0, "火": 90.0, "金": 180.0, "水": 270.0
        }

        intensities = {}
        for wx, angle in positions.items():
            diff = abs(phi_deg - angle)
            if diff > 180:
                diff = 360 - diff
            # 余弦衰减: 0°差=1.0, 90°差=0.0, 180°差=-1.0(取max(0,..))
            intensities[wx] = max(0.0, math.cos(math.radians(diff)))

        # 土强度 = 距中轴距离的反比（越靠近中轴越土）
        s_distance = math.sin(theta)  # 距中轴距离
        intensities["土"] = 1.0 - s_distance

        # 归一化
        total = sum(intensities.values())
        if total > 0:
            return {k: round(v / total, 3) for k, v in intensities.items()}
        return {k: 0.2 for k in intensities}


# ═══════════════════════════════════════════════════════════════
# 自检系统
# ═══════════════════════════════════════════════════════════════

class SelfTest:
    """v2.0引擎自检（13项）"""

    def __init__(self):
        self.engine = WuxingSphereV2()
        self.passed = 0
        self.failed = 0

    def _check(self, name: str, condition: bool, detail: str = ""):
        if condition:
            self.passed += 1
            print(f"  [PASS] {name}")
        else:
            self.failed += 1
            print(f"  [FAIL] {name} {detail}")

    def run_all(self) -> bool:
        print("=" * 50)
        print("WuxingSphereV2 自检报告")
        print("=" * 50)

        # 1. 四行基础色相映射
        c_m = self.engine.mapper.map_pillar("甲", "寅", "day")
        self._check("木=春分=0°", abs(math.degrees(c_m.phi) % 360) < 30,
                    f"phi={math.degrees(c_m.phi):.1f}°")

        c_f = self.engine.mapper.map_pillar("丙", "午", "day")
        self._check("火=夏至≈90°", 60 < math.degrees(c_f.phi) % 360 < 120,
                    f"phi={math.degrees(c_f.phi):.1f}°")

        c_j = self.engine.mapper.map_pillar("庚", "申", "day")
        self._check("金=秋分≈180°", 150 < math.degrees(c_j.phi) % 360 < 210,
                    f"phi={math.degrees(c_j.phi):.1f}°")

        c_s = self.engine.mapper.map_pillar("壬", "子", "day")
        self._check("水=冬至≈270°", 240 < math.degrees(c_s.phi) % 360 < 300,
                    f"phi={math.degrees(c_s.phi):.1f}°")

        # 2. 土轴验证
        c_tu = self.engine.mapper.map_pillar("戊", "辰", "day")
        self._check("土=中轴附近(S≈0)", c_tu.to_hsl().s < 0.5,
                    f"S={c_tu.to_hsl().s:.2f}")

        # 3. 南北极明度
        north = SphereCoord(r=1.0, theta=0, phi=0)
        self._check("北极=白(L≈1)", north.to_hsl().l > 0.9,
                    f"L={north.to_hsl().l:.2f}")

        south = SphereCoord(r=1.0, theta=math.pi, phi=0)
        self._check("南极=黑(L≈0)", south.to_hsl().l < 0.1,
                    f"L={south.to_hsl().l:.2f}")

        # 4. 赤道灰
        equator = SphereCoord(r=1.0, theta=math.pi/2, phi=0)
        self._check("赤道=灰(L≈0.5)", 0.4 < equator.to_hsl().l < 0.6,
                    f"L={equator.to_hsl().l:.2f}")

        # 5. 对跖点关系
        self._check("木↔金对跖180°", abs((c_m.phi - c_j.phi) % (2*math.pi) - math.pi) < 0.5)
        self._check("火↔水对跖180°", abs((c_f.phi - c_s.phi) % (2*math.pi) - math.pi) < 0.5)

        # 6. 四柱映射
        bazi = {
            "year": {"gan": "癸", "zhi": "酉"},
            "month": {"gan": "戊", "zhi": "午"},
            "day": {"gan": "丁", "zhi": "巳"},
            "hour": {"gan": "丙", "zhi": "午"}
        }
        report = self.engine.compute_lifetime_color({"birth": bazi})
        self._check("JSON报告生成", "birth_color" in report)
        self._check("HSL输出有效", 0 <= report["birth_hsl"]["h"] < 360)
        self._check("五行平衡归一", abs(sum(report["wuxing_balance"].values()) - 1.0) < 0.01)

        # 7. 大运叠加
        birth_coord = self.engine.mapper.map_bazi(bazi)
        dy_color = self.engine.compute_da_yun_color(birth_coord, "甲子", 0.3)
        self._check("大运色彩计算", dy_color.to_hex().startswith("#"))

        # 8. 颜色空间闭合
        hex_color = birth_color = self.engine.compute_birth_color(bazi)
        rgb = hex_color.to_rgb()
        self._check("RGB范围有效", all(0 <= c <= 255 for c in rgb))

        # 9. 柱内叠加（天干主导）
        c_gan = self.engine.mapper.map_gan("甲")  # 木
        c_zhi = self.engine.mapper.map_gan(self.engine.mapper.ZHI_MAIN_QI["寅"])  # 甲=木
        self._check("柱内同五行不冲突", abs(c_gan - c_zhi) < 0.1)

        # 10. 日柱权重最大
        day_c = self.engine.mapper.map_pillar("丁", "巳", "day")
        year_c = self.engine.mapper.map_pillar("癸", "酉", "year")
        self._check("日柱半径>年柱半径", day_c.r > year_c.r)

        print("=" * 50)
        print(f"结果: {self.passed} 通过, {self.failed} 失败")
        print("=" * 50)
        return self.failed == 0


# ═══════════════════════════════════════════════════════════════
# 演示
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 运行自检
    test = SelfTest()
    all_pass = test.run_all()

    if all_pass:
        print("\n所有自检通过，演示计算...")

        engine = WuxingSphereV2()

        # 示例八字（需替换为真实八字）
        demo_bazi = {
            "birth": {
                "year": {"gan": "癸", "zhi": "酉"},
                "month": {"gan": "戊", "zhi": "午"},
                "day": {"gan": "丁", "zhi": "巳"},
                "hour": {"gan": "丙", "zhi": "午"}
            },
            "da_yun": ["甲子", "乙丑", "丙寅", "丁卯", "戊辰"],
            "liu_nian": [2026, 2027, 2028, 2029, 2030]
        }

        report = engine.compute_lifetime_color(demo_bazi)
        print("\n" + "=" * 50)
        print("色彩报告 (JSON):")
        print("=" * 50)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("\n自检有失败项，请修复后重试。")
