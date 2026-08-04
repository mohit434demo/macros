# Pantry data sources

Values in `site/pantry.js`. Verified 2026-08-03.

## Gram staples (per 100 g)

| Food | Cal | P | C | F | Source |
|---|---|---|---|---|---|
| White Rice (cooked) | 130 | 2.7 | 28.2 | 0.3 | USDA FDC 168878, "Rice, white, long-grain, regular, enriched, cooked". |
| Brown Rice (cooked) | 123 | 2.7 | 25.6 | 1.0 | USDA SR Legacy, long-grain brown rice, cooked. |
| Chicken Thigh (cooked) | 209 | 26 | 0 | 10.9 | USDA SR Legacy, chicken thigh, meat only, roasted. Cooked weight, not raw. |
| Chicken Breast (cooked) | 165 | 31 | 0 | 3.6 | USDA SR Legacy, chicken breast, meat only, roasted. |

Raw boneless skinless thigh runs about 120 to 145 cal per 100 g; cooking drives
off roughly 25 to 30 percent water, which concentrates it to the 209 figure.
Weigh **after** cooking to use these values.

## Cooking add-ons

| Food | Serving | Cal | P | C | F | Note |
|---|---|---|---|---|---|---|
| Olive Oil | tsp | 40 | 0 | 0 | 4.5 | 1 Tbsp = 3 tsp = 120 cal |
| Chicken Bouillon | cube/tsp | 10 | 0.5 | 1 | 0.5 | Varies by brand |
| Chicken Stock | cup | 15 | 2 | 1 | 0.5 | Low-sodium carton stock |
| Butter | tsp | 34 | 0 | 0 | 3.9 | |
| Sauce / Marinade add-on | 10 cal | 10 | 0 | 1 | 0.6 | Free-form: enter total calories, split as a typical sauce |

## Packaged

| Food | Serving | Cal | P | C | F | Source |
|---|---|---|---|---|---|---|
| Dave's Killer Bread White Bun | 1 bun (62 g) | 160 | 8 | 30 | 1.5 | Open Food Facts `0001376402824`. Protein confirmed by user. |
| Turkey Deli Meat | 3 oz | 90 | 20 | 2 | 0.5 | Calories and protein from user's package. |
| Ham Deli Meat | 3 oz | 90 | 18 | 2 | 1 | Calories and protein from user's package. |
| Ayoh Dill Pickle Mayo | 1 Tbsp (14 g) | 60 | 0 | 0 | 7 | Open Food Facts, brand "Ayoh". |
| Kraft American Cheese Slice | 1 slice (21 g) | 60 | 3 | 2 | 4.5 | Open Food Facts, regular Singles. |
| PopCorners Kettle Corn | 1 oz (28 g) | 130 | 2 | 21 | 4.5 | Open Food Facts, "Sweet & Salty Kettle Corn". |
| BERO Shandy | 1 can | 90 | 0 | 21 | 0 | Calories from user. Carbs inferred. |

## Saved meals

**Sandwich Meal** (546 cal, 48 g protein): 5.5 oz deli meat split evenly, 1 bun,
half a tablespoon of Ayoh, 1 cheese slice, 1 bag of PopCorners.

Derived from its parts, so correcting a component updates the meal.

There is deliberately no saved rice-and-chicken plate: those portions change
day to day, so the app instead remembers the last gram amount used for each
staple and pre-fills it.

## Accuracy stance

The user's guidance is that a well-educated estimate is acceptable. Gram
staples come from USDA SR Legacy where checked (rice and chicken were verified
directly); the rest of the library uses standard reference values for common
preparations. Everything is correctable in-app, so a wrong value is a
15-second fix rather than a redeploy.

## Items to double check against a package

- BERO Shandy carbohydrates (inferred, not read from a label)
- Deli turkey and ham carbohydrate/fat (only calories and protein were supplied)
- Bouillon and stock vary widely by brand

Any of these can be corrected in the app (open the item, "Correct these
numbers") without a redeploy.

