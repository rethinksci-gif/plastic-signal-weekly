# Plastic Signal UI refresh — 2026-09-28

## References

- https://github.com/withastro/starlight — latest commit checked via GitHub API: 2026-09-28, `[ci] format`. Reference for accessible reading controls and documentation navigation.
- https://github.com/just-the-docs/just-the-docs — latest commit checked via GitHub API: 2026-09-23, dependency maintenance for selenium-webdriver. Reviewed `_sass/layout.scss` for bounded reading width and responsive sidebar patterns.

These are interaction and layout references; no source code was copied and no framework dependency was added.

## Changes

- Own Jekyll layout for home and reading pages, replacing the globally stretched Cayman presentation.
- Persistent masthead, direct issue/coverage/RSS navigation, keyboard skip link.
- Latest issues placed immediately after the hero; shorter hero and section spacing.
- Existing cream/green editorial identity retained with light, dark and system appearance controls.
- Standard/large reading text, stored locally when browser storage is available.
- Bounded article measure, generated section navigation, accessible focus indicators and reduced-motion handling.
- Removed hard-coded week number. Existing RSS and issue data remain driven by Jekyll.

## Validation

- `node --check docs/assets/js/signal.js` and `git diff --check` passed.
- Temporary HTML previews assembled from the new layout and the existing published issue listing; article content converted with Python Markdown.
- Headless Chrome: home/article at 1440, 390 and 320 pixels, no horizontal overflow; four article section links generated; dark/large settings persisted across reload; no runtime exceptions.
- Desktop and mobile screenshots visually reviewed.
- This is not a full Jekyll build: Ruby/Jekyll were unavailable locally. GitHub Pages build and deployment remain unverified. Changes have not been pushed.
