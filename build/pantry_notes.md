# Pantry data sources

Values in `site/pantry.js`. Verified 2026-08-03.

| Food | Serving | Cal | P | C | F | Source |
|---|---|---|---|---|---|---|
| Dave's Killer Bread White Bun | 1 bun (62 g) | 160 | 8 | 30 | 1.5 | Open Food Facts `0001376402824`, "Burgers Done Right Organic White Bread Hamburger Buns". Protein confirmed by user. |
| Turkey Deli Meat | 3 oz | 90 | 20 | 2 | 0.5 | Calories and protein supplied by user from package. Carbs/fat are typical deli-turkey values. |
| Ham Deli Meat | 3 oz | 90 | 18 | 2 | 1 | Calories and protein supplied by user from package. Carbs/fat are typical deli-ham values. |
| Ayoh Dill Pickle Mayo | 1 Tbsp (14 g) | 60 | 0 | 0 | 7 | Open Food Facts, brand "Ayoh", product "Dill Pickle Mayo". |
| Kraft American Cheese Slice | 1 slice (21 g) | 60 | 3 | 2 | 4.5 | Open Food Facts, "American Singles Pasteurized Prepared Cheese Product", Kraft. Regular Singles, not 2% or Deli Deluxe. |
| PopCorners Kettle Corn | 1 oz (28 g) | 130 | 2 | 21 | 4.5 | Open Food Facts, PopCorners "Sweet & Salty Kettle Corn", consistent across several entries. |
| BERO Shandy | 1 can | 90 | 0 | 21 | 0 | Calories supplied by user. Carbohydrate inferred from calories (shandy has no fat or protein). Not verified against a label. |

## Sandwich Meal

5.5 oz deli meat split evenly (0.92 x 3 oz turkey + 0.92 x 3 oz ham), 1 bun,
half a tablespoon of Ayoh dill pickle mayo, 1 cheese slice, 1 bag of PopCorners.

Derived at runtime from the parts, so correcting any component updates the meal.

## Items to double check against a package

- BERO Shandy carbohydrates (inferred, not read from a label)
- Deli turkey and ham carbohydrate/fat (only calories and protein were supplied)

Any of these can be corrected in the app under More, My foods, without a redeploy.
