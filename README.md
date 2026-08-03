# Macros

A phone-first nutrition tracker built as an installable PWA. Log meals from a
built-in cookbook, track macros against a cutting target, and watch body
recomposition through weight and waist trends with an adaptive maintenance
estimate.

## Features

- **Today** - calorie ring, protein/carb/fat bars, meals split into
  breakfast/lunch/dinner/snack, quick portion scaling (0.5x to 2x or any
  fraction). Swipe left/right to move between days.
- **Cookbook** - 70 recipes with full ingredients and instructions. Filter by
  protein type or format, sort by calories-per-gram-of-protein, calories, or
  protein.
- **Progress** - daily weight and waist entry, 7-day rolling average trend
  charts, and an adaptive maintenance calculation that back-solves your real
  TDEE from actual intake versus actual trend-weight change.
- **Offline first** - installs to the home screen and works with no connection.

## Privacy

All personal data (food logs, weights, measurements, targets) is stored in
`localStorage` on your device only. Nothing is uploaded, and this repository
contains no personal data. Use **More > Export data** to back up.

## Development

```
python build/extract.py   # parse source recipe PDFs -> data/recipes.json
python build/bundle.py    # data/recipes.json -> site/recipes.js
python build/icons.py     # regenerate app icons
python build/test_app.py  # end-to-end browser tests (needs local server)
```

Serve locally with `python -m http.server 8777` from `site/`.
