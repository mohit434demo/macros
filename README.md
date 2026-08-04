# Macros

A phone-first nutrition tracker built as an installable PWA. Log meals from a
built-in cookbook, track macros against a cutting target, and watch body
recomposition through weight and waist trends with an adaptive maintenance
estimate.

## Features

- **Today** - calorie ring, protein/carb/fat bars, meals split into
  breakfast/lunch/dinner/snack, quick portion scaling (0.5x to 2x or any
  fraction). A "Quick add" strip repeats your usual foods in one tap. Swipe
  left/right between days, or tap the date for a month calendar showing which
  days you logged and how close you were to target.
- **Earned shortlist** - the Add sheet opens to just the foods you actually eat.
  Anything logged once joins the list automatically, ordered by most recent.
  Searching always falls through to the full library, and items can be marked
  "want to try", "in rotation", or "not for me".
- **Everyday pantry** - bundled packaged foods (buns, deli meat, condiments,
  snacks) plus saved meals that combine them. Meal macros are derived from
  their components, so correcting one component updates every meal using it.
  Any bundled value can be corrected on-device without a redeploy.
- **Cookbook** - 120 recipes from two sources, each with full ingredients and
  instructions. The 70 Stealth Health recipes link to the original publisher
  PDF and, where available, the recipe video. The 50 Joe x Fitness recipes are
  Korean and Asian-inspired, tagged by category (meal prep, 30-minute, high
  protein, viral, banchan, soups). Filter by book, cuisine, rotation status or
  protein type; sort by calories-per-gram-of-protein, calories, or protein.
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
python build/extract.py      # parse Stealth Health PDFs -> data/recipes.json
python build/extract_joe.py  # parse the Joe x Fitness cookbook -> data/joe_recipes.json
python build/bundle.py       # merge both -> site/recipes.js
python build/icons.py        # regenerate app icons
python build/test_app.py     # end-to-end browser tests (needs local server)
```

Serve locally with `python -m http.server 8777` from `site/`.
