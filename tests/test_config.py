#!/usr/bin/env python3
"""Unit tests for persistent configuration management."""
import pytest
from config import DashboardConfig, ALL_PAGE_IDS

def test_default_config():
    cfg = DashboardConfig()
    assert cfg.minitoo_port == "AUTO"
    assert cfg.rotation_interval == 4.0
    assert cfg.auto_cycle is False
    assert cfg.dgx_host == "dgx"
    assert len(cfg.page_order) == len(ALL_PAGE_IDS)
    for p_id in ALL_PAGE_IDS:
        assert p_id in cfg.page_order
        assert p_id in cfg.enabled_pages

def test_config_serialization():
    cfg = DashboardConfig(
        minitoo_port="COM9",
        rotation_interval=8.0,
        dgx_host="my-gpu-node",
    )
    d = cfg.to_dict()
    assert d["minitoo_port"] == "COM9"
    assert d["rotation_interval"] == 8.0
    assert d["dgx_host"] == "my-gpu-node"

    loaded = DashboardConfig.from_dict(d)
    assert loaded.minitoo_port == "COM9"
    assert loaded.rotation_interval == 8.0
    assert loaded.dgx_host == "my-gpu-node"
