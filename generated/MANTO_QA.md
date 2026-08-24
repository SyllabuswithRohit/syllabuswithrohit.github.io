# Manto Stories — Automated QA

These files are complete machine-assisted first passes and require independent human review.

| Work | Source chars | Output chars | Devanagari left | Urdu left | Roman-only |
|---|---:|---:|---:|---:|---|
| Khol Do | 5,908 | 7,622 | 0 | 0 | PASS |
| Thanda Gosht | 10,784 | 13,964 | 0 | 0 | PASS |

## Failures

- Toba Tek Singh: RuntimeError: Roman-only check failed: Devanagari=9, Urdu=0
- Bu: RuntimeError: Roman-only check failed: Devanagari=1, Urdu=0
- Kali Shalwar: RuntimeError: Roman-only check failed: Devanagari=3, Urdu=0
- Hatak: RuntimeError: Roman-only check failed: Devanagari=8, Urdu=0
- Naya Qanoon: RuntimeError: Roman-only check failed: Devanagari=5, Urdu=0
- Tetwal Ka Kutta: RuntimeError: Roman-only check failed: Devanagari=1, Urdu=0
