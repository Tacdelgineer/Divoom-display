#!/usr/bin/env python3
"""Unit tests for subprocess execution helper."""
import sys
import pytest
from subproc import check_output_hidden, run_hidden

def test_run_hidden_basic():
    # Echo test should succeed and capture output cleanly
    res = run_hidden([sys.executable, "-c", "print('hello_hidden')"], capture_output=True, text=True, timeout=5.0)
    assert res.returncode == 0
    assert "hello_hidden" in res.stdout

def test_check_output_hidden_basic():
    out = check_output_hidden([sys.executable, "-c", "print('test_output')"], text=True, timeout=5.0)
    assert "test_output" in out
