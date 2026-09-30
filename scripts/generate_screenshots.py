"""
Script to generate clean repo screenshots for Milestone 13:
- assets/screenshots/preset-ai.png
- assets/screenshots/preset-crypto.png
- assets/screenshots/preset-stocks.png
- assets/screenshots/preset-system.png
- assets/screenshots/preset-all.png
- assets/screenshots/settings-dashboard.png
- assets/screenshots/settings-minitoo.png
"""
import os
import sys
import time
import tkinter as tk
from PIL import ImageGrab

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    DashboardConfig,
    PRESET_ALL,
    PRESET_AI,
    PRESET_CRYPTO,
    PRESET_STOCKS,
    PRESET_SYSTEM,
)
from dashboard_app import DesktopDashboardApp
from ui_components import SettingsDialog


def capture_window(widget, out_path):
    widget.update_idletasks()
    widget.update()
    time.sleep(0.3)
    widget.update_idletasks()
    widget.update()

    x = widget.winfo_rootx()
    y = widget.winfo_rooty()
    w = widget.winfo_width()
    h = widget.winfo_height()

    bbox = (x, y, x + w, y + h)
    img = ImageGrab.grab(bbox=bbox)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    print(f"Captured: {out_path} ({w}x{h})")


def main():
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "screenshots")

    # 1. Capture Presets
    presets = [
        (PRESET_ALL, "preset-all.png"),
        (PRESET_AI, "preset-ai.png"),
        (PRESET_CRYPTO, "preset-crypto.png"),
        (PRESET_STOCKS, "preset-stocks.png"),
        (PRESET_SYSTEM, "preset-system.png"),
    ]

    for p_name, filename in presets:
        root = tk.Tk()
        # Ensure dummy position on primary display
        root.geometry("640x600+100+100")
        app = DesktopDashboardApp(root)
        app.config.apply_preset(p_name)
        app.focus_section = None
        app._render_gui()

        out_path = os.path.join(assets_dir, filename)
        capture_window(root, out_path)
        app.engine.stop()
        app.minitoo.stop()
        app.ditoo.stop()
        root.destroy()
        time.sleep(0.2)

    # 2. Capture Settings Dialog - DASHBOARD Tab
    root = tk.Tk()
    root.geometry("640x600+100+100")
    app = DesktopDashboardApp(root)
    app.config.apply_preset(PRESET_ALL)
    app._render_gui()

    settings_dlg = SettingsDialog(root, app.config, minitoo=app.minitoo, state=app.state)
    settings_dlg.geometry("780x560+120+120")
    settings_dlg._switch_tab(settings_dlg.TAB_DASHBOARD)
    out_dash = os.path.join(assets_dir, "settings-dashboard.png")
    capture_window(settings_dlg, out_dash)

    # 3. Capture Settings Dialog - MINITOO Tab
    settings_dlg._switch_tab(settings_dlg.TAB_MINITOO)
    out_mini = os.path.join(assets_dir, "settings-minitoo.png")
    capture_window(settings_dlg, out_mini)

    settings_dlg._on_close()
    app.engine.stop()
    app.minitoo.stop()
    app.ditoo.stop()
    root.destroy()
    print("All screenshots generated successfully!")


if __name__ == "__main__":
    main()
