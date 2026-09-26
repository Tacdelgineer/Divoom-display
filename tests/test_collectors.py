#!/usr/bin/env python3
"""Unit tests for collectors and hardware detector."""
import pytest
from collectors import LocalPcCollector, ServicesCollector, BtcCollector
from detector import detect_minitoo_port, get_all_com_ports

def test_local_pc_collector():
    collector = LocalPcCollector()
    data = collector.collect()
    assert data.page_id == "local_pc"
    assert data.title == "LOCAL PC"
    # RAM and CPU should always be collected via psutil
    assert data.secondary_metric is not None
    assert data.secondary_metric.label == "RAM"
    assert len(data.extra_metrics) >= 1
    assert data.extra_metrics[0].label == "CPU"

def test_services_collector_fallback():
    # Test that services collector handles unreachable host without throwing
    collector = ServicesCollector(dgx_host="invalid-host-unreachable-9999", cache_file=".test_services_cache.json")
    data = collector.collect()
    assert data.page_id == "services"
    assert "UP" in data.badge
    import os
    if os.path.exists(".test_services_cache.json"):
        os.remove(".test_services_cache.json")

def test_detector_safe_when_no_device():
    # Auto-detection should return a string (if device connected) or None, never raise
    port = detect_minitoo_port()
    assert port is None or isinstance(port, str)

def test_get_all_com_ports():
    ports = get_all_com_ports()
    assert isinstance(ports, list)
