---
name: check
description: Review 用户刚写的代码：跑测试和检查，按教练模式给反馈，不贴修复代码。完成后更新进度。
disable-model-invocation: true
---

1. `git status` 和 `git diff`（含未暂存的新文件）看用户改了什么。
2. 在 `backend/` 下跑 `uv run ruff check .`、`uv run mypy app tests`、`uv run pytest -q`，报告结果。
3. 按 CLAUDE.md 的 Review 顺序给反馈：正确性 bug → 面试追问点 → 可读性。每条带 `文件:行号`，只说问题和方向。
4. 如果当前任务卡的完成标准已达到：在 `docs/progress.md` 勾上对应项，追加一行日期和学到的概念；
   然后问用户一个这块代码相关的面试题，等用户回答后再点评。
5. 没达到就说清楚还差什么。
