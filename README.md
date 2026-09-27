# Plastic Signal Weekly

An automated weekly intelligence brief for plastics innovation teams.

**Website:** [rethinksci-gif.github.io/plastic-signal-weekly](https://rethinksci-gif.github.io/plastic-signal-weekly/)

It tracks eight decision-focused pillars: market and business trends, sustainable materials, recycling technologies, material performance, future materials, supply and feedstocks, regulation and compliance, and research and patents.

Each signal is translated into four editorial blocks: what changed, why it matters, practical implication, and a proportionate next action.

## Run locally

```bash
uv sync
export DEEPSEEK_API_KEY=your_key
uv run horizon --hours 168
```

## GitHub setup

1. Open **Settings → Secrets and variables → Actions** in the repository.
2. Add a repository secret named `DEEPSEEK_API_KEY` containing a newly created DeepSeek API key.
3. Open **Settings → Pages** and set the source to **Deploy from a branch** using `gh-pages` and `/ (root)`.
4. Run the **Plastic Signal Weekly** workflow manually once, or wait for the schedule.

The scheduled GitHub Action runs every Sunday at 06:00 UTC, generates an English weekly brief from the previous 168 hours, and publishes the archive to GitHub Pages.

基于 [Horizon](https://github.com/Thysrael/Horizon) 构建（MIT License）。
