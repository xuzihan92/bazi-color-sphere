# 八字色彩引擎 pytest 测试报告

> **报告编号**: BAZI-COLOR-TEST-2026-06-27  
> **测试对象**: 八字色彩引擎 v2.1（`wuxing_sphere_v2.1.py`）  
> **数据基线**: `ganzhi_sphere_map_v1.3.json`  
> **测试日期**: 2026-06-27  
> **执行人**: 工成  
> **审查人**: 审言（06-27 20:52 签字确认）  
> **终检人**: 存真（06-27 23:51 终检通过）

---

## 1. 执行摘要

| 指标 | 结果 |
|------|------|
| 总用例数 | 42 |
| 通过 | 42 |
| 失败 | 0 |
| 跳过 | 0 |
| **通过率** | **100%** |
| 核心文件覆盖率 | 75%（目标 20%，超额完成） |
| 金标准回归 | 7/7 全绿 |

**结论**: 八字色彩引擎 pytest 测试套件全部通过，金标准锁定有效，可进入下一阶段。

---

## 2. 测试环境

| 项目 | 值 |
|------|-----|
| 操作系统 | Windows 11 (Windows_NT 10.0.26200) |
| Python 版本 | 3.12.10 |
| pytest 版本 | 9.1.1 |
| pytest-cov 版本 | 7.1.0 |
| 工作目录 | `E:\AI\U-Claw\data\.openclaw\workspace-team\玄学部\八字色彩` |
| 测试命令 | `python -m pytest tests/ -v --cov=. --cov-report=term-missing` |

---

## 3. 测试分层

| 测试文件 | 用例数 | 覆盖范围 |
|----------|--------|----------|
| `tests/test_data_layer.py` | 15 | JSON 数据完整性、60 干支查表、H/S/L/T 范围、五行色区 |
| `tests/test_engine_logic.py` | 20 | HSL 转换、圆形色相混合、日主色计算、大运叠加、五行平衡 |
| `tests/test_regression.py` | 7 | 金标准回归：梓涵本命色锁定 |
| **合计** | **42** | — |

---

## 4. 金标准回归结果

| 检查项 | 期望值 | 实际值 | 状态 |
|--------|--------|--------|------|
| 本命 HEX | `#7C202F` | `#7C202F` | ✅ |
| 色相 H | 350.1998° | 350.1998° | ✅ |
| 色相区间 | 红区（330°–360° / 0°–30°） | 红区 | ✅ |
| 色温 T | 4575K | 4575K | ✅ |
| 饱和度 S | 对应金标准 | 通过 | ✅ |
| 明度 L | 对应金标准 | 通过 | ✅ |
| 五行主导 | 火主导 | 通过 | ✅ |

> 金标准一旦失败，代表引擎行为发生变化，必须阻断提交。

---

## 5. 核心代码覆盖率

| 文件 | 语句数 | 未覆盖 | 覆盖率 |
|------|--------|--------|--------|
| `wuxing_sphere_v2.1.py` | 257 | 63 | **75%** |

**未覆盖行说明**（主要为核心创新边界与异常分支）：
- 99-102, 106-109: 五行计算边界分支
- 174: 异常处理分支
- 193-194, 197: 调试/辅助输出
- 421: 大运强度边界
- 458-461, 512-514: 特殊干支处理
- 568: 强度归一边界
- 580-582, 585-590, 593-670: 报告输出与辅助函数

其余 `_pdf_generator.py`、`_test_xuzihan_bazi.py`、`_zip_archive.py`、`wuxing_sphere_v2.py` 为旧版/工具脚本，不计入核心覆盖率目标。

---

## 6. 测试明细

### 6.1 数据层测试（`tests/test_data_layer.py`）

| 用例 | 状态 |
|------|------|
| `test_json_loads` | ✅ PASSED |
| `test_records_count` | ✅ PASSED |
| `test_records_required_fields` | ✅ PASSED |
| `test_records_no_duplicate_ganzhi` | ✅ PASSED |
| `test_hsl_value_ranges` | ✅ PASSED |
| `test_color_temperature_range` | ✅ PASSED |
| `test_earth_pillar_h_is_null` | ✅ PASSED |
| `test_fire_pillars_h_in_red_zone` | ✅ PASSED |
| `test_water_pillars_h_in_blue_zone` | ✅ PASSED |
| `test_lookup_bingwu` | ✅ PASSED |
| `test_lookup_renxu` | ✅ PASSED |
| `test_lookup_jiayou_earth` | ✅ PASSED |
| `test_lookup_invalid_raises` | ✅ PASSED |
| `test_lookup_gan_zhi_api` | ✅ PASSED |
| `test_all_60_pillars_loadable` | ✅ PASSED |

### 6.2 引擎逻辑测试（`tests/test_engine_logic.py`）

| 用例 | 状态 |
|------|------|
| `test_hsl_to_hex_white` | ✅ PASSED |
| `test_hsl_to_hex_black` | ✅ PASSED |
| `test_hsl_to_hex_red` | ✅ PASSED |
| `test_hsl_clamp_overflow` | ✅ PASSED |
| `test_hsl_hex_format` | ✅ PASSED |
| `test_circular_average_boundary` | ✅ PASSED |
| `test_water_fire_mix_reasonable` | ✅ PASSED |
| `test_earth_excluded_from_h_average` | ✅ PASSED |
| `test_all_earth_returns_none_h` | ✅ PASSED |
| `test_birth_color_returns_all_fields` | ✅ PASSED |
| `test_birth_color_pillar_count` | ✅ PASSED |
| `test_birth_color_pillar_weights` | ✅ PASSED |
| `test_partial_bazi_still_works` | ✅ PASSED |
| `test_dayun_returns_hex` | ✅ PASSED |
| `test_dayun_intensity_bounds` | ✅ PASSED |
| `test_dayun_full_intensity` | ✅ PASSED |
| `test_wuxing_balance_sums_to_one` | ✅ PASSED |
| `test_wuxing_balance_all_five_present` | ✅ PASSED |
| `test_wuxing_balance_no_negative` | ✅ PASSED |
| `test_metal_present_from_dizhi` | ✅ PASSED |

### 6.3 回归测试（`tests/test_regression.py`）

| 用例 | 状态 |
|------|------|
| `test_regression_hex_exact` | ✅ PASSED |
| `test_regression_hue_zone` | ✅ PASSED |
| `test_regression_hue_precise` | ✅ PASSED |
| `test_regression_color_temperature` | ✅ PASSED |
| `test_regression_saturation` | ✅ PASSED |
| `test_regression_lightness` | ✅ PASSED |
| `test_regression_fire_dominant` | ✅ PASSED |

---

## 7. 警告与备注

| 类型 | 内容 | 处理意见 |
|------|------|----------|
| ⚠️ 警告 | pytest 10 弃用警告：`class-scoped fixture` 不建议定义为 instance method | 不影响当前功能；建议在后续重构中改用 `@classmethod` 装饰器 |

---

## 8. 签字

| 角色 | 姓名 | 时间 | 意见 |
|------|------|------|------|
| 执行 | 工成 | 2026-06-27 20:14 | 42/42 通过，金标准锁定 |
| 审查 | 审言 | 2026-06-27 20:52 | ✅ 通过，签字结项 |
| 终检 | 存真 | 2026-06-27 23:51 | ✅ 通过，建议补充本报告文件 |

---

## 9. 变更记录

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| v1.0 | 2026-06-27 | 初版，基于 pytest 9.1.1 全量执行结果 | 工成 |
