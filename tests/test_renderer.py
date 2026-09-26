#!/usr/bin/env python3
"""Unit tests for Pillow framebuffer rendering."""
import pytest
from PIL import Image
from models import PageData, MetricItem
from renderer import render_dashboard_page

def test_render_dashboard_page():
    page = PageData(
        page_id="test",
        title="TEST",
        badge="ACTIVE",
        badge_color="green",
        primary_metric=MetricItem(label="5H", value="85% LEFT", remaining_pct=85.0),
        secondary_metric=MetricItem(label="WEEK", value="90% LEFT", remaining_pct=90.0),
        footer_left="PLUS",
        footer_right="GPT-4O",
    )
    img = render_dashboard_page(page, page_num=1, total_pages=5)
    assert isinstance(img, Image.Image)
    assert img.size == (128, 128)
    assert img.mode == "RGB"

def test_render_btc_page():
    page = PageData(
        page_id="btc",
        title="BITCOIN",
        badge="+3.5%",
        badge_color="green",
        sparkline_data=[100.0, 110.0, 105.0, 120.0, 130.0, 125.0, 140.0],
        footer_left="$96,000",
        footer_right="24H",
    )
    img = render_dashboard_page(page)
    assert isinstance(img, Image.Image)
    assert img.size == (128, 128)
