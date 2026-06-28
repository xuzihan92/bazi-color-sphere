"""
pytest 配置 & 公共 fixture
"""
import importlib.util
import os
import sys

import pytest

# 确保引擎文件可被 import（文件名含点，用 importlib 加载）
ENGINE_PATH = os.path.join(os.path.dirname(__file__), "..", "wuxing_sphere_v2.1.py")
JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "ganzhi_sphere_map_v1.3.json")


def _load_engine():
    spec = importlib.util.spec_from_file_location("wuxing_engine", os.path.abspath(ENGINE_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# 模块级缓存，避免每次 fixture 都重新解析 JSON
_ENGINE_MODULE = None


def get_engine_module():
    global _ENGINE_MODULE
    if _ENGINE_MODULE is None:
        _ENGINE_MODULE = _load_engine()
    return _ENGINE_MODULE


@pytest.fixture(scope="session")
def engine_module():
    """返回引擎模块（整个测试会话共享一次加载）"""
    return get_engine_module()


@pytest.fixture(scope="session")
def engine(engine_module):
    """返回 WuxingSphereV21 实例"""
    return engine_module.WuxingSphereV21()


@pytest.fixture(scope="session")
def mapper(engine_module):
    """返回 SichenPillarMapper 实例"""
    return engine_module.SichenPillarMapper()


# ─── 梓涵八字（壬申 己酉 丁未 丙午）─────────────────────────────
XUZIHAN_BAZI = {
    "year": {"gan": "壬", "zhi": "申"},
    "month": {"gan": "己", "zhi": "酉"},
    "day": {"gan": "丁", "zhi": "未"},
    "hour": {"gan": "丙", "zhi": "午"},
}

# 金标准值（v1.3 JSON + v2.1 引擎验证，2026-06-26 存真终检通过）
XUZIHAN_GOLD = {
    "hex": "#7C202F",
    "H_min": 345.0,   # 色相允许区间下限
    "H_max": 355.0,   # 色相允许区间上限
    "H_exact": 350.1998306632618,
    "T": 4575.0,
    "S": 0.583,
    "L": 0.309,
}
