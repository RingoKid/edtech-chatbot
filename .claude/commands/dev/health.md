---
description: Quick health check — backend, frontend, OpenAI key, and AWS services
---

# /dev health

**Run mode:** inline (no agent needed). Run the health check script and show its output.

Run this script:
```bash
bash .claude/scripts/health-check.sh
```

Show the output as-is. If the exit code is non-zero, some checks failed — note which ones have ⚠️ and suggest next steps (e.g., "run `/dev devops logs` to investigate backend").

Keep it tight — no extra commentary unless something is wrong.
