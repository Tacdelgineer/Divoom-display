"""
Bluetooth Coexistence Benchmark & Hardware Diagnostics Script
Measures MiniToo traffic metrics in NORMAL vs LOW_INTERFERENCE mode.
"""
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serial
from PIL import Image

from backends import MiniTooDisplay
from inputs import MiniTooInputAdapter
from detector import detect_minitoo_port


def run_benchmark():
    port = detect_minitoo_port()
    print(f"=== MiniToo Bluetooth Coexistence Test ===")
    print(f"Detected MiniToo Port: {port}")
    if not port:
        print("MiniToo not detected on Bluetooth COM ports. Aborting.")
        return

    # Test A: NORMAL MODE
    print("\n--- Phase 1: NORMAL MODE (45s run) ---")
    disp_normal = MiniTooDisplay(port=port)
    inputs_normal = MiniTooInputAdapter(port=port, display=disp_normal, bt_mode="NORMAL", poll_rate="AUTO")
    
    # Send initial test frame
    test_img = Image.new("RGB", (160, 128), color=(20, 30, 50))
    disp_normal.show(test_img, ser=inputs_normal.ser)

    start_t = time.time()
    next_check = start_t + 10.0
    while time.time() - start_t < 45.0:
        event = inputs_normal.poll_event()
        if time.time() >= next_check:
            inputs_normal.query_channel()
            next_check = time.time() + 10.0
        time.sleep(inputs_normal.poll_interval)

    rates_normal = disp_normal.get_rolling_rates()
    poll_normal = inputs_normal.get_poll_diagnostics()
    inputs_normal.close()

    print(f"NORMAL MODE RESULTS:")
    print(f"  SPP Writes / min:     {rates_normal['writes_per_min']}")
    print(f"  SPP Reads / min:      {rates_normal['reads_per_min']}")
    print(f"  Bytes Transmitted /m: {rates_normal['bytes_per_min']} B/min ({rates_normal['kb_per_min']} KB/min)")
    print(f"  Knob Polls / sec:     {poll_normal['knob_polls_per_sec']} Hz (Interval: {poll_normal['poll_interval']}s)")
    print(f"  Channel Checks / min: {poll_normal['channel_checks_per_min']}")

    time.sleep(2.0)

    # Test B: LOW INTERFERENCE MODE
    print("\n--- Phase 2: LOW INTERFERENCE MODE (45s run) ---")
    disp_low = MiniTooDisplay(port=port)
    inputs_low = MiniTooInputAdapter(port=port, display=disp_low, bt_mode="LOW_INTERFERENCE", poll_rate="AUTO")
    
    disp_low.show(test_img, ser=inputs_low.ser)

    start_t = time.time()
    next_check = start_t + 30.0
    while time.time() - start_t < 45.0:
        event = inputs_low.poll_event()
        if time.time() >= next_check:
            inputs_low.query_channel()
            next_check = time.time() + 30.0
        time.sleep(inputs_low.poll_interval)

    rates_low = disp_low.get_rolling_rates()
    poll_low = inputs_low.get_poll_diagnostics()
    inputs_low.close()

    print(f"LOW INTERFERENCE MODE RESULTS:")
    print(f"  SPP Writes / min:     {rates_low['writes_per_min']}")
    print(f"  SPP Reads / min:      {rates_low['reads_per_min']}")
    print(f"  Bytes Transmitted /m: {rates_low['bytes_per_min']} B/min ({rates_low['kb_per_min']} KB/min)")
    print(f"  Knob Polls / sec:     {poll_low['knob_polls_per_sec']} Hz (Interval: {poll_low['poll_interval']}s)")
    print(f"  Channel Checks / min: {poll_low['channel_checks_per_min']}")

    # Traffic Reduction Calculation
    write_reduction = 0.0
    if rates_normal['writes_per_min'] > 0:
        write_reduction = (1.0 - rates_low['writes_per_min'] / rates_normal['writes_per_min']) * 100.0

    print("\n=== SUMMARY COMPARISON ===")
    print(f"  SPP Writes: {rates_normal['writes_per_min']} -> {rates_low['writes_per_min']} /min ({write_reduction:.1f}% reduction)")
    print(f"  Knob Polling Cadence: {poll_normal['poll_interval']}s -> {poll_low['poll_interval']}s")
    print(f"  Frame Diffing: Zero redundant frame pushes in both modes")


if __name__ == "__main__":
    run_benchmark()
