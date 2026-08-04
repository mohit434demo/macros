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

  { id: "s-ground-beef-93", n: "Ground Beef 93/7 (cooked)", unit: "100 g", per100: true,
    cal: 182, p: 25, c: 0, f: 9, tags: ["staple", "protein"] },

  { id: "s-ground-turkey", n: "Ground Turkey 93/7 (cooked)", unit: "100 g", per100: true,
    cal: 176, p: 27, c: 0, f: 8, tags: ["staple", "protein"] },

  { id: "s-steak", n: "Steak, sirloin (cooked)", unit: "100 g", per100: true,
    cal: 206, p: 29, c: 0, f: 9, tags: ["staple", "protein"] },

  { id: "s-pork-tenderloin", n: "Pork Tenderloin (cooked)", unit: "100 g", per100: true,
    cal: 143, p: 26, c: 0, f: 4, tags: ["staple", "protein"] },

  { id: "s-salmon", n: "Salmon (cooked)", unit: "100 g", per100: true,
    cal: 208, p: 22, c: 0, f: 13, tags: ["staple", "protein"] },

  { id: "s-white-fish", n: "White Fish / Tilapia (cooked)", unit: "100 g", per100: true,
    cal: 128, p: 26, c: 0, f: 2.7, tags: ["staple", "protein"] },

  { id: "s-shrimp", n: "Shrimp (cooked)", unit: "100 g", per100: true,
    cal: 99, p: 24, c: 0, f: 0.3, tags: ["staple", "protein"] },

  { id: "s-tofu", n: "Tofu, firm", unit: "100 g", per100: true,
    cal: 144, p: 17, c: 3, f: 9, tags: ["staple", "protein"] },

  { id: "s-paneer", n: "Paneer", unit: "100 g", per100: true,
    cal: 296, p: 18, c: 4, f: 23, tags: ["staple", "protein"] },

  { id: "s-egg", n: "Egg, large", unit: "egg",
    cal: 72, p: 6.3, c: 0.4, f: 4.8, tags: ["staple", "protein"] },

  { id: "s-egg-white", n: "Egg White", unit: "white",
    cal: 17, p: 3.6, c: 0.2, f: 0, tags: ["staple", "protein"] },

  { id: "s-whey", n: "Whey Protein", unit: "scoop",
    cal: 120, p: 24, c: 3, f: 1.5, tags: ["staple", "protein"] },

  // ---------------------------------------------------------- carbs
  { id: "s-pasta", n: "Pasta (cooked)", unit: "100 g", per100: true,
    cal: 158, p: 5.8, c: 31, f: 0.9, tags: ["staple", "grain"] },

  { id: "s-quinoa", n: "Quinoa (cooked)", unit: "100 g", per100: true,
    cal: 120, p: 4.4, c: 21, f: 1.9, tags: ["staple", "grain"] },

  { id: "s-potato", n: "Potato (cooked)", unit: "100 g", per100: true,
    cal: 87, p: 2, c: 20, f: 0.1, tags: ["staple", "veg"] },

  { id: "s-sweet-potato", n: "Sweet Potato (cooked)", unit: "100 g", per100: true,
    cal: 90, p: 2, c: 21, f: 0.1, tags: ["staple", "veg"] },

  { id: "s-black-beans", n: "Black Beans (cooked)", unit: "100 g", per100: true,
    cal: 132, p: 8.9, c: 24, f: 0.5, tags: ["staple", "veg"] },

  { id: "s-chickpeas", n: "Chickpeas (cooked)", unit: "100 g", per100: true,
    cal: 164, p: 8.9, c: 27, f: 2.6, tags: ["staple", "veg"] },

  { id: "s-lentils", n: "Lentils / Dal (cooked)", unit: "100 g", per100: true,
    cal: 116, p: 9, c: 20, f: 0.4, tags: ["staple", "veg"] },

  { id: "s-oats", n: "Oats (dry)", unit: "40 g scoop",
    cal: 152, p: 5.3, c: 27, f: 2.6, tags: ["staple", "grain"] },

  { id: "s-bread-slice", n: "Bread, slice", unit: "slice",
    cal: 80, p: 4, c: 14, f: 1, tags: ["staple", "bread"] },

  { id: "s-tortilla", n: "Flour Tortilla, medium", unit: "tortilla",
    cal: 140, p: 4, c: 24, f: 3.5, tags: ["staple", "bread"] },

  { id: "s-roti", n: "Roti / Chapati", unit: "roti",
    cal: 120, p: 3, c: 22, f: 2.5, tags: ["staple", "bread"] },

  // ---------------------------------------------------------- dairy and fats
  { id: "s-greek-yogurt", n: "Greek Yogurt, 0%", unit: "100 g", per100: true,
    cal: 59, p: 10, c: 3.6, f: 0.4, tags: ["staple", "dairy"] },

  { id: "s-cottage-cheese", n: "Cottage Cheese, 2%", unit: "100 g", per100: true,
    cal: 84, p: 11, c: 4.3, f: 2.3, tags: ["staple", "dairy"] },

  { id: "s-shredded-cheese", n: "Shredded Cheese", unit: "1 oz",
    cal: 113, p: 7, c: 0.4, f: 9, tags: ["staple", "dairy"] },

  { id: "s-milk-2", n: "Milk, 2%", unit: "cup",
    cal: 122, p: 8, c: 12, f: 4.8, tags: ["staple", "dairy"] },

  { id: "s-peanut-butter", n: "Peanut Butter", unit: "Tbsp",
    cal: 94, p: 3.5, c: 3.5, f: 8, tags: ["staple", "fat"] },

  { id: "s-avocado", n: "Avocado", unit: "100 g", per100: true,
    cal: 160, p: 2, c: 9, f: 15, tags: ["staple", "fat"] },

  { id: "s-almonds", n: "Almonds", unit: "1 oz",
    cal: 164, p: 6, c: 6, f: 14, tags: ["staple", "fat"] },

  // ---------------------------------------------------------- produce
  { id: "s-broccoli", n: "Broccoli (cooked)", unit: "100 g", per100: true,
    cal: 35, p: 2.4, c: 7, f: 0.4, tags: ["staple", "veg"] },

  { id: "s-mixed-veg", n: "Mixed Vegetables (cooked)", unit: "100 g", per100: true,
    cal: 45, p: 2.2, c: 9, f: 0.3, tags: ["staple", "veg"] },

  { id: "s-salad-greens", n: "Salad Greens", unit: "100 g", per100: true,
    cal: 23, p: 2.2, c: 3.6, f: 0.4, tags: ["staple", "veg"] },

  { id: "s-banana", n: "Banana, medium", unit: "banana",
    cal: 105, p: 1.3, c: 27, f: 0.4, tags: ["staple", "fruit"] },

  { id: "s-apple", n: "Apple, medium", unit: "apple",
    cal: 95, p: 0.5, c: 25, f: 0.3, tags: ["staple", "fruit"] },

  { id: "s-berries", n: "Berries", unit: "100 g", per100: true,
    cal: 57, p: 0.7, c: 14, f: 0.3, tags: ["staple", "fruit"] },

  // ------------------------------------------------- cooking add-ons
  { id: "s-olive-oil", n: "Olive Oil", unit: "tsp",
    cal: 40, p: 0, c: 0, f: 4.5, tags: ["staple", "addon", "fat"] },

  { id: "s-bouillon", n: "Chicken Bouillon", unit: "cube/tsp",
    cal: 10, p: 0.5, c: 1, f: 0.5, tags: ["staple", "addon"] },

  { id: "s-chicken-stock", n: "Chicken Stock", unit: "cup",
    cal: 15, p: 2, c: 1, f: 0.5, tags: ["staple", "addon"] },

  { id: "s-butter", n: "Butter", unit: "tsp",
    cal: 34, p: 0, c: 0, f: 3.9, tags: ["staple", "addon", "fat"] },

  { id: "s-soy-sauce", n: "Soy Sauce", unit: "Tbsp",
    cal: 9, p: 1, c: 1, f: 0, tags: ["staple", "addon"] },

  { id: "s-honey", n: "Honey", unit: "Tbsp",
    cal: 64, p: 0, c: 17, f: 0, tags: ["staple", "addon"] },

  { id: "s-ketchup", n: "Ketchup", unit: "Tbsp",
    cal: 19, p: 0, c: 5, f: 0, tags: ["staple", "addon"] },

  { id: "s-hot-sauce", n: "Hot Sauce / Sriracha", unit: "tsp",
    cal: 5, p: 0, c: 1, f: 0, tags: ["staple", "addon"] },

  // Free-form calorie add-on for a marinade, sauce or dressing whose macros
  // you do not know. Logged in calories; the app splits them sensibly.
  { id: "s-sauce-addon", n: "Sauce / Marinade add-on", unit: "10 cal", freeCal: true,
    cal: 10, p: 0, c: 1, f: 0.6, tags: ["staple", "addon", "sauce"] },

  // Eating out: enter your best calorie estimate, split as a mixed meal.
  { id: "s-meal-estimate", n: "Restaurant / Unknown Meal", unit: "10 cal", freeCal: true,
    cal: 10, p: 0.5, c: 1.1, f: 0.4, tags: ["staple", "addon", "sauce"] },

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
];
