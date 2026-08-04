// Starter pantry: everyday packaged foods, gram-based staples, and saved meals.
// Nutrition-facts data only, no personal information.
// Sources noted in build/pantry_notes.md.
//
// `per100: true` means the macros below are PER 100 GRAMS and the app asks for
// a gram weight instead of a serving multiplier.
const PANTRY = [
  // ---------------------------------------------------------- gram staples
  { id: "s-rice-white", n: "White Rice (cooked)", unit: "100 g", per100: true,
    cal: 130, p: 2.7, c: 28.2, f: 0.3, tags: ["staple", "grain"] },

  { id: "s-rice-brown", n: "Brown Rice (cooked)", unit: "100 g", per100: true,
    cal: 123, p: 2.7, c: 25.6, f: 1.0, tags: ["staple", "grain"] },

  { id: "s-chicken-thigh", n: "Chicken Thigh (cooked)", unit: "100 g", per100: true,
    cal: 209, p: 26, c: 0, f: 10.9, tags: ["staple", "protein"] },

  { id: "s-chicken-breast", n: "Chicken Breast (cooked)", unit: "100 g", per100: true,
    cal: 165, p: 31, c: 0, f: 3.6, tags: ["staple", "protein"] },

  // ------------------------------------------------- cooking add-ons
  { id: "s-olive-oil", n: "Olive Oil", unit: "tsp",
    cal: 40, p: 0, c: 0, f: 4.5, tags: ["staple", "addon", "fat"] },

  { id: "s-bouillon", n: "Chicken Bouillon", unit: "cube/tsp",
    cal: 10, p: 0.5, c: 1, f: 0.5, tags: ["staple", "addon"] },

  { id: "s-chicken-stock", n: "Chicken Stock", unit: "cup",
    cal: 15, p: 2, c: 1, f: 0.5, tags: ["staple", "addon"] },

  { id: "s-butter", n: "Butter", unit: "tsp",
    cal: 34, p: 0, c: 0, f: 3.9, tags: ["staple", "addon", "fat"] },

  // Free-form calorie add-on for a marinade, sauce or dressing whose macros
  // you do not know. Logged in calories; the app splits them sensibly.
  { id: "s-sauce-addon", n: "Sauce / Marinade add-on", unit: "10 cal", freeCal: true,
    cal: 10, p: 0, c: 1, f: 0.6, tags: ["staple", "addon", "sauce"] },

  // ---------------------------------------------------------- packaged
  { id: "p-dkb-white-bun", n: "Dave's Killer Bread White Bun", unit: "bun",
    cal: 160, p: 8, c: 30, f: 1.5, tags: ["pantry", "bread"] },

  { id: "p-deli-turkey", n: "Turkey Deli Meat", unit: "3 oz",
    cal: 90, p: 20, c: 2, f: 0.5, tags: ["pantry", "protein"] },

  { id: "p-deli-ham", n: "Ham Deli Meat", unit: "3 oz",
    cal: 90, p: 18, c: 2, f: 1, tags: ["pantry", "protein"] },

  { id: "p-ayoh-dill", n: "Ayoh Dill Pickle Mayo", unit: "Tbsp",
    cal: 60, p: 0, c: 0, f: 7, tags: ["pantry", "condiment"] },

  { id: "p-kraft-single", n: "Kraft American Cheese Slice", unit: "slice",
    cal: 60, p: 3, c: 2, f: 4.5, tags: ["pantry", "dairy"] },

  { id: "p-popcorners-kettle", n: "PopCorners Kettle Corn", unit: "1 oz bag",
    cal: 130, p: 2, c: 21, f: 4.5, tags: ["pantry", "snack"] },

  { id: "p-bero-shandy", n: "BERO Shandy (non-alc)", unit: "can",
    cal: 90, p: 0, c: 21, f: 0, tags: ["pantry", "drink"] },

  // ---------------------------------------------------------- saved meals
  { id: "p-sandwich-meal", n: "Sandwich Meal", unit: "meal",
    tags: ["pantry", "meal"],
    parts: [
      { id: "p-deli-turkey", qty: 0.92 },   // 2.75 oz
      { id: "p-deli-ham", qty: 0.92 },      // 2.75 oz
      { id: "p-dkb-white-bun", qty: 1 },
      { id: "p-ayoh-dill", qty: 0.5 },      // small spritz
      { id: "p-kraft-single", qty: 1 },
      { id: "p-popcorners-kettle", qty: 1 },
    ] },

  { id: "s-rice-chicken-plate", n: "Rice & Chicken Thigh Plate", unit: "meal",
    tags: ["staple", "meal"],
    parts: [
      { id: "s-rice-white", qty: 1.5 },       // 150 g
      { id: "s-chicken-thigh", qty: 3.1 },    // 310 g
      { id: "s-sauce-addon", qty: 8 },        // 80 cal of marinade
    ] },
];
