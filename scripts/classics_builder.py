#!/usr/bin/env python3
from pathlib import Path

out = Path('generated')
out.mkdir(parents=True, exist_ok=True)
(out / 'SMOKE.md').write_text('# Smoke\n\nPublic GitHub Actions runner and Python dependency installation worked.\n', encoding='utf-8')
print('smoke complete')
