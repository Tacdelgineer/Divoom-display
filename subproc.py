#!/usr/bin/env python3
"""
Windows-Safe Hidden Subprocess Utility for AI Desk Dashboard.

Ensures all background CLI invocations (nvidia-smi, ssh, git, agy, codex, etc.)
execute with NO visible console or CMD windows, preventing application flickering
and focus-stealing when running as a windowed Windows executable.
"""
from __future__ import annotations

import sys
import subprocess
from typing import Any, List, Optional, Union, Dict

# On Windows:
# CREATE_NO_WINDOW = 0x08000000 prevents console window creation.
# STARTF_USESHOWWINDOW + SW_HIDE ensures any child console window is hidden.
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
STARTF_USESHOWWINDOW = getattr(subprocess, "STARTF_USESHOWWINDOW", 0x00000001)
SW_HIDE = getattr(subprocess, "SW_HIDE", 0)


def get_hidden_subprocess_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Apply Windows-safe creationflags and startupinfo to ensure child console
    applications execute completely in the background without creating a window.
    """
    params = dict(kwargs)
    if sys.platform == "win32":
        # 1. Ensure CREATE_NO_WINDOW flag is set
        cflags = params.get("creationflags", 0)
        cflags |= CREATE_NO_WINDOW
        params["creationflags"] = cflags

        # 2. Ensure STARTUPINFO specifies SW_HIDE
        si = params.get("startupinfo")
        if si is None:
            si = subprocess.STARTUPINFO()
        si.dwFlags |= STARTF_USESHOWWINDOW
        si.wShowWindow = SW_HIDE
        params["startupinfo"] = si

    return params


def run_hidden(cmd: Union[str, List[str]], **kwargs) -> subprocess.CompletedProcess:
    """
    Execute subprocess.run with Windows console window suppression.
    Defaults shell=False for security and clean direct execution.
    """
    safe_kwargs = get_hidden_subprocess_kwargs(**kwargs)
    if "shell" not in safe_kwargs:
        safe_kwargs["shell"] = False
    return subprocess.run(cmd, **safe_kwargs)


def check_output_hidden(cmd: Union[str, List[str]], **kwargs) -> Union[str, bytes]:
    """
    Execute subprocess.check_output with Windows console window suppression.
    Defaults shell=False for security and clean direct execution.
    """
    safe_kwargs = get_hidden_subprocess_kwargs(**kwargs)
    if "shell" not in safe_kwargs:
        safe_kwargs["shell"] = False
    return subprocess.check_output(cmd, **safe_kwargs)


def Popen_hidden(cmd: Union[str, List[str]], **kwargs) -> subprocess.Popen:
    """
    Execute subprocess.Popen with Windows console window suppression.
    Defaults shell=False for security and clean direct execution.
    """
    safe_kwargs = get_hidden_subprocess_kwargs(**kwargs)
    if "shell" not in safe_kwargs:
        safe_kwargs["shell"] = False
    return subprocess.Popen(cmd, **safe_kwargs)
