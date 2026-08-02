## Items Present

### Mundane
- Stretched animal hides (various stages of curing)
- Barrels of dye and oil
- Tanning tools

### For Sale
- Cured leather (per yard): 5 sp
- Leather scraps (bag): 2 sp
- Custom leather goods: price by item and complexity, 2-7 days

## Notes for DM
- Boren knows which local farmers have been losing livestock — he processes what remains after predation
- He will share this information if asked directly; he does not volunteer it

---

## Runtime Containers

These containers are authoritative for stock placement and access.

| id | name | owner | access | affordances |
|---|---|---|---|---|
| merchant_stock | Merchant stock displays | boren | public | container |

## Runtime Things

This table is the authoritative runtime inventory for this place.

| id | name | emoji | container | owner | price | category | affordances | availability | effect |
|---|---|---|---|---|---|---|---|---|---|
| cured_leather_per_yard | Cured leather (per yard) |  | merchant_stock | boren | 5 sp | mundane | holdable | public |  |
| leather_scraps_bag | Leather scraps (bag) |  | merchant_stock | boren | 2 sp | mundane | holdable | public |  |
| custom_leather_goods | Custom leather goods |  |  | boren | 2-7 gp; 2-7 days | service |  | public |  |
