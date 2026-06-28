#!/usr/bin/env python3
"""
许梓涵八字色彩报告测试
"""
import json
from wuxing_sphere_v2 import WuxingSphereV2

sphere = WuxingSphereV2()

# 许梓涵八字：壬申 己酉 丁未 丙午
bazi_data = {
    "birth": {
        "year":  {"gan": "壬", "zhi": "申"},
        "month": {"gan": "己", "zhi": "酉"},
        "day":   {"gan": "丁", "zhi": "未"},
        "hour":  {"gan": "丙", "zhi": "午"}
    },
    "da_yun": ["壬戌", "癸亥", "甲子", "乙丑", "丙寅"],
    "liu_nian": [2024, 2025, 2026, 2027, 2028]
}

# 计算本命色彩
report = sphere.compute_lifetime_color(bazi_data)

# 打印完整报告
print("=" * 60)
print("【许梓涵 · 八字色彩报告】")
print("=" * 60)
print()

# 八字信息
print("【八字】")
print(f"  年柱: 壬申 (水·金)")
print(f"  月柱: 己酉 (土·金)")
print(f"  日柱: 丁未 (火·土)")
print(f"  时柱: 丙午 (火·火)")
print()

# 本命色彩
print("【本命色彩】")
print(f"  HEX: {report['birth_color']}")
hsl = report['birth_hsl']
print(f"  HSL: H={hsl['h']:.1f}°, S={hsl['s']:.3f}, L={hsl['l']:.3f}")
coord = report['birth_coord']
print(f"  坐标: r={coord['r']:.3f}, theta={coord['theta_deg']:.1f}°, phi={coord['phi_deg']:.1f}°")
print()

# 五行平衡
print("【五行平衡】")
for wx, pct in report["wuxing_balance"].items():
    bar = "█" * int(pct * 20)
    print(f"  {wx}: {pct*100:.1f}% {bar}")
print()

# 坐标解读
print("【球体定位解读】")
theta = coord['theta_deg']
phi = coord['phi_deg']
if theta < 30:
    print(f"  中轴位置: 北极附近 (巽4·土之极阳·白)")
elif theta < 60:
    print(f"  中轴位置: 北半球偏上 (偏白)")
elif theta < 120:
    print(f"  中轴位置: 赤道附近 (灰)")
elif theta < 150:
    print(f"  中轴位置: 南半球偏下 (偏黑)")
else:
    print(f"  中轴位置: 南极附近 (乾6·土之极阴·黑)")

if 0 <= phi < 45 or 315 <= phi <= 360:
    print(f"  黄道方位: 春分附近 (木·震3)")
elif 45 <= phi < 135:
    print(f"  黄道方位: 夏至附近 (火·离9)")
elif 135 <= phi < 225:
    print(f"  黄道方位: 秋分附近 (金·兑7)")
else:
    print(f"  黄道方位: 冬至附近 (水·坎1)")
print()

# 大运色彩
print("【大运色彩】")
for i, dy in enumerate(report["da_yun_colors"]):
    print(f"  第{i+1}步运: {dy['ganzhi']} {dy['color']} {dy['hsl']} (强度:{dy['intensity']})")
print()

# 四柱分项
print("【四柱分项色彩】")
for pt, pc in report["pillar_colors"].items():
    print(f"  {pt}: {pc['gan']}{pc['zhi']} → {pc['color']} {pc['hsl']}")
print()

# 完整JSON
print("【完整JSON报告】")
print(json.dumps(report, ensure_ascii=False, indent=2))
