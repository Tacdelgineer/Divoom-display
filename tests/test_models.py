#!/usr/bin/env python3
"""Unit tests for normalized dashboard data models."""
import pytest
from models import PageData, MetricItem
from providers import UsageData

def test_metric_item_remaining_semantics():
    m = MetricItem(
        label="5H",
        value="75% LEFT",
        pct=25.0,
        remaining_pct=75.0,
        authority="AUTHORITATIVE",
    )
    assert m.remaining_pct == 75.0
    assert m.value == "75% LEFT"
    assert m.authority == "AUTHORITATIVE"

def test_usage_data_normalization():
    u = UsageData(
        provider_name="Codex",
        primary_label="5H",
        primary_pct=25,
        primary_reset="2H",
        primary_status="ACTIVE",
        secondary_label="WEEK",
        secondary_pct=18,
        secondary_reset="4D",
        model="GPT-4O",
        plan_tier="PLUS",
        raw_primary_value="25%",
        raw_primary_semantic="USED",
        normalized_primary_used=25,
        normalized_primary_remaining=75,
        authority="AUTHORITATIVE",
    )
    assert u.normalized_primary_remaining == 75
    assert u.normalized_primary_used == 25
    assert not u.is_stale

def test_pagedata_defaults():
    p = PageData(
        page_id="test",
        title="TEST",
        badge="ACTIVE",
        badge_color="green",
    )
    assert p.page_id == "test"
    assert p.primary_metric is None
    assert p.sparkline_data is None
