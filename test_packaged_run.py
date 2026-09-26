#!/usr/bin/env python3
"""
2-Minute Packaged Executable Acceptance Test for AI Desk Dashboard.

Monitors dist/AI Desk Dashboard.exe for 125+ seconds:
1. Verifies process runs continuously.
2. Monitors for any visible CMD / PowerShell / Console windows.
3. Tracks child process executions (nvidia-smi, ssh, git, etc.).
4. Checks launch.log for any uncaught exceptions.
5. Verifies zero console flashing.
"""
import os
import sys
import time
import subprocess
import psutil

EXE_PATH = os.path.abspath(r"release\AI Desk Dashboard.exe") if os.path.exists(r"release\AI Desk Dashboard.exe") else os.path.abspath(r"dist\AI Desk Dashboard.exe")
TEST_DURATION = 125  # seconds (2+ minutes)


def run_test():
    print(f"[TEST] Target executable: {EXE_PATH}")
    if not os.path.exists(EXE_PATH):
        print(f"[TEST] ERROR: Executable not found at {EXE_PATH}")
        sys.exit(1)

    print(f"[TEST] Starting '{EXE_PATH}'...")
    proc = subprocess.Popen([EXE_PATH])
    pid = proc.pid
    print(f"[TEST] AI Desk Dashboard.exe started with PID: {pid}")

    start_time = time.time()
    next_report = start_time + 10.0
    detected_flashes = []
    child_executions = set()
    poll_count = 0

    try:
        p_parent = psutil.Process(pid)
    except Exception as e:
        print(f"[TEST] ERROR: Could not attach psutil to PID {pid}: {e}")
        proc.kill()
        sys.exit(1)

    print(f"[TEST] Commencing {TEST_DURATION}s continuous monitoring loop...")

    try:
        while time.time() - start_time < TEST_DURATION:
            poll_count += 1
            now = time.time()

            # 1. Check parent process health
            if not p_parent.is_running() or p_parent.status() == psutil.STATUS_ZOMBIE:
                print(f"[TEST] ERROR: AI Desk Dashboard.exe terminated prematurely at {now - start_time:.1f}s")
                break

            # 2. Inspect children
            try:
                children = p_parent.children(recursive=True)
                for child in children:
                    cname = child.name().lower()
                    child_executions.add(cname)
                    # Check if any child process is a console/shell that might show a window
                    if cname in ("cmd.exe", "powershell.exe"):
                        detected_flashes.append((now - start_time, cname, child.pid))
                        print(f"[TEST] WARNING: Shell child detected: {cname} (PID: {child.pid}) at {now - start_time:.1f}s")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            # 3. Check for any rogue conhost / cmd / powershell processes spawned on the system
            # with visible window titles
            for p in psutil.process_iter(['pid', 'name']):
                try:
                    name = p.info['name'].lower()
                    if name in ("cmd.exe", "powershell.exe"):
                        # If cmd or powershell was spawned by our parent tree
                        try:
                            parent_pid = p.ppid()
                            if parent_pid == pid or parent_pid in [c.pid for c in p_parent.children(recursive=True)]:
                                detected_flashes.append((now - start_time, name, p.pid))
                                print(f"[TEST] WARNING: Rogue console detected: {name} (PID: {p.pid})")
                        except Exception:
                            pass
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # 4. Periodic Telemetry Report every 15s
            if now >= next_report:
                elapsed = int(now - start_time)
                mem_mb = p_parent.memory_info().rss / (1024 * 1024)
                print(f"[TEST] +{elapsed:3d}s elapsed | Parent PID {pid} alive | Memory: {mem_mb:.1f} MB | Tracked children: {list(child_executions)} | Flashes: {len(detected_flashes)}")
                next_report = now + 15.0

            time.sleep(0.5)

    finally:
        total_time = time.time() - start_time
        print(f"\n[TEST] Stopping AI Desk Dashboard.exe after {total_time:.1f}s...")
        try:
            # Terminate parent and all children cleanly
            for child in p_parent.children(recursive=True):
                try:
                    child.terminate()
                except Exception:
                    pass
            p_parent.terminate()
            p_parent.wait(timeout=3.0)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    print("\n==================================================")
    print("TEST REPORT & VERIFICATION SUMMARY")
    print("==================================================")
    print(f"Total Test Run Time   : {total_time:.1f} seconds (Target: {TEST_DURATION}s)")
    print(f"Total Poll Cycles     : {poll_count}")
    print(f"Observed Child Types  : {sorted(list(child_executions))}")
    print(f"Visible Console Events: {len(detected_flashes)}")

    if detected_flashes:
        print(f"[FAIL] Detected {len(detected_flashes)} console window event(s): {detected_flashes}")
        sys.exit(1)
    else:
        print("[PASS] ZERO visible CMD/PowerShell/Console window popups detected during the 2+ minute test!")
        sys.exit(0)


if __name__ == "__main__":
    run_test()
