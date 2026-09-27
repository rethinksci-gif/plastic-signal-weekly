# Plastic Signal Weekly

An automated weekly intelligence brief for plastics innovation teams.

**Website:** [rethinksci-gif.github.io/plastic-signal-weekly](https://rethinksci-gif.github.io/plastic-signal-weekly/)

It tracks eight decision-focused pillars: market and business trends, sustainable materials, recycling technologies, material performance, future materials, supply and feedstocks, regulation and compliance, and research and patents.

Each signal is translated into four editorial blocks: what changed, why it matters, practical implication, and a proportionate next action.

## Sources and editorial selection

Sixteen feeds combine direct publisher content with focused seven-day searches:

- PlasticsToday: materials, applications, manufacturing and business; full article extraction when accessible.
- Resource Recycling: recycled-material markets, policy and operations; full feed articles.
- European Bioplastics: association announcements and policy positions, attributed to the association.
- Nature polymer subject feed: publication links with original article and abstract extraction when accessible.
- Twelve targeted Google News searches: design, PCR, recycling, performance, emerging materials, resin markets, EU/US/China regulation, research, suppliers and industrialization. Official EU and US regulatory domains receive dedicated searches.

Feeds were checked on 27 September 2026. Selection requires explicit plastics relevance and a score of at least 5/10, keeps up to five items per pillar and 24 overall, and removes repeated coverage of the same event. General metals, battery and e-scrap stories do not qualify without a substantive plastics connection in the source. The category is assigned from article content. Every issue begins with up to five takeaways from distinct covered pillars. Missing evidence is not filled in to reach a quota; resin prices require a sourced grade, region, unit and date.

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

Based on [Horizon](https://github.com/Thysrael/Horizon) and [AIM4R](https://github.com/rethinksci-gif/AIM4R) (MIT License).
