#!/usr/bin/env python3
import zipfile
import os
from pathlib import Path

base_dir = Path("E:/AI/U-Claw/data/.openclaw/workspace-team/cards/八字色彩")
zip_path = base_dir.parent / "八字色彩_完整归档_20260607.zip"

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for item in base_dir.rglob('*'):
        arcname = str(item.relative_to(base_dir))
        zf.write(item, arcname)

size = zip_path.stat().st_size
print(f"ZIP created: {zip_path}")
print(f"Size: {size} bytes")
