#!/usr/bin/env python3
"""
Interactive hardware acceptance test for physical knob navigation on Divoom MiniToo.
Presents dashboard pages and responds immediately to physical knob rotations:
- Knob Clockwise -> NEXT PAGE
- Knob Counter-Clockwise -> PREVIOUS PAGE
"""
import time
import sys
from inputs import MiniTooInputAdapter, InputEvent
from backends import get_display_backend
from dashboard import collect_page
from renderer import render_dashboard_page

PAGES = ["btc", "claude", "codex", "gemini"]

def run_knob_test(duration: float = 120.0):
    print("=" * 68)
    print("  PHYSICAL KNOB NAVIGATION ACCEPTANCE TEST")
    print("=" * 68)
    print(f"Target: Auto-detect | Test Duration: {duration}s")
    print("Instructions:")
    print("  1. Watch the physical MiniToo screen.")
    print("  2. Turn the volume knob CLOCKWISE: the screen should advance to NEXT page.")
    print("  3. Turn the volume knob COUNTER-CLOCKWISE: the screen should go to PREVIOUS page.")
    print("  4. Notice the screen stays in Dashboard mode without reverting to Clock.")
    print("-" * 68)

    adapter = MiniTooInputAdapter()
    if not adapter.ser or not adapter.ser.is_open:
        print("Failed to open MiniToo connection.")
        return

    display = get_display_backend("minitoo")
    current_idx = 0
    total = len(PAGES)

    def show_current():
        p_key = PAGES[current_idx]
        data = collect_page(p_key)
        img = render_dashboard_page(data, page_num=current_idx + 1, total_pages=total)
        print(f"\n[{time.strftime('%H:%M:%S')}] Rendering [{current_idx + 1}/{total}] {data.title.upper()} -> MiniToo LCD...")
        display.show(img, ser=adapter.ser)
        print(f"[{time.strftime('%H:%M:%S')}] Visible on screen: {data.title.upper()}. Turn knob now!")

    show_current()

    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            event = adapter.poll_event()
            if event == InputEvent.NEXT_PAGE:
                current_idx = (current_idx + 1) % total
                print(f"\n>>> KNOB CLOCKWISE DETECTED -> Advancing to [{current_idx + 1}/{total}] {PAGES[current_idx].upper()}")
                show_current()
            elif event == InputEvent.PREV_PAGE:
                current_idx = (current_idx - 1) % total
                print(f"\n>>> KNOB COUNTER-CLOCKWISE DETECTED -> Going back to [{current_idx + 1}/{total}] {PAGES[current_idx].upper()}")
                show_current()
            time.sleep(0.04)
    except KeyboardInterrupt:
        print("\nTest stopped by user.")
    finally:
        adapter.close()
        print("\nTest completed.")

if __name__ == "__main__":
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
    run_knob_test(dur)
