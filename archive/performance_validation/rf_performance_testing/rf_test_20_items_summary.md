# 20 Random Items for Performance and Result Testing

This file contains 20 randomly selected items from the GET /items/ endpoint for performance and result testing between the original (port 8080) and refactored (port 8081) containers.

## Selection Method
- Used Python's random.sample() with seed=42 for reproducible results
- Selected from the complete items dataset (1,939 total items)
- Both endpoints return identical data for these items

## Selected Items

| Item ID | Product Name | Country | Group | Subgroup | Proxy |
|---------|--------------|---------|-------|----------|-------|
| 11032-FRA | Basil, dried | France | cooking aids and various ingredients | spices | false |
| 11045-BRA | Baker's yeast, dehydrated | Brazil | cooking aids and various ingredients | miscellaneous ingredients | false |
| 11163-ESP | Sweet and sour sauce, prepacked | Spain | cooking aids and various ingredients | condiments | false |
| 12737-FRA | Mimolette cheese, half-old, from cow's milk | France | milk and dairy products | other cheese products | false |
| 12834-FRA | Crottin de Chavignol cheese, from goat's milk | France | milk and dairy products | other cheese products | false |
| 13731-FRA | Peach, canned in light syrup, not drained | France | fruits, vegetables, legumes and oilseeds | fruits | false |
| 15006-FRA | Coconut, ripe kernel, fresh | France | fruits, vegetables, legumes and oilseeds | nuts and oilseeds | false |
| 19026-FRA | Condensed milk, without sugar, whole | France | milk and dairy products | milk and other milk products | false |
| 20039-FRA | Leek, raw | France | fruits, vegetables, legumes and oilseeds | vegetables | false |
| 20904-FRA | Tofu, plain | France | fruits, vegetables, legumes and oilseeds | legumes | false |
| 25123-FRA | Moussaka | France | mixed dishes | dish from various origins | false |
| 26091-FRA | Mullet, raw | France | meats, eggs, fish | fish | false |
| 26270-FRA | Pizza, tuna | France | mixed dishes | dish from various origins | false |
| 31102-FRA | Cereal bar with chocolate, fortified with vitamins and minerals | France | sugary products | cereal bars | false |
| 4020-FRA | Dauphine potato, frozen, raw | France | fruits, vegetables, legumes and oilseeds | vegetables | false |
| 51510-FRA | Frik (crushed immature durum wheat), raw | France | cereal products | pasta, rice and cereals | false |
| 7650-FRA | Croissant w almonds, from bakery | France | cereal products | viennoseries and pastries | false |
| 9380-FRA | Buckwheat, whole, raw | France | cereal products | pasta, rice and cereals | false |
| 9621-FRA | Wheat bran | France | cooking aids and various ingredients | miscellaneous ingredients | false |
| 9640-FRA | Oat bran | France | cooking aids and various ingredients | miscellaneous ingredients | false |

## Data Files Created

1. **rf_test_20_items_original.json** - Items from original endpoint (port 8080)
2. **rf_test_20_items_refactored.json** - Items from refactored endpoint (port 8081)
3. **rf_random_20_items_original.json** - Full original response (1,939 items)
4. **rf_random_20_items_refactored_fixed.json** - Full refactored response (1,939 items)

## Validation Results

✅ **Data Consistency Verified**
- All 20 items found in both endpoints
- Data identical between original and refactored endpoints
- Item counts match (20/20)

## Usage for Testing

These items can be used for:
1. Performance testing of GET /items/ endpoint
2. Input for POST /calculate-recipe/ endpoint testing
3. Baseline validation between container versions
4. Result consistency verification

## Next Steps

Use these item IDs as input for testing the POST /calculate-recipe/ endpoint to compare:
- Response times between containers
- Calculation result consistency
- API response structure validation