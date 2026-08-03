// Starter pantry: everyday packaged foods and saved meals.
// Nutrition-facts data only, no personal information.
// Sources noted in build/pantry_notes.md.
const PANTRY = [
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

  // Saved meal: macros are derived from the parts above.
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
];
