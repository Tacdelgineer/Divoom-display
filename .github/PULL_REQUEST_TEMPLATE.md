## Description
Briefly describe the intent and changes made in this pull request.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Performance / Reliability improvement
- [ ] Documentation update
- [ ] Refactoring (no functional changes)

## Checklist
- [ ] Code compiles cleanly (`python -m compileall .`)
- [ ] Existing functionality and desktop mode are preserved
- [ ] No machine-specific paths, private IPs, credentials, or tokens are included
- [ ] On Windows, all child subprocesses use `subproc.py` (no visible console popups)
- [ ] If hardware-related: verified safe fallback when MiniToo hardware is disconnected
- [ ] Tests and terminal status check run successfully (`python dashboard.py --status`)
