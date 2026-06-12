# Shajara original rasm V3 import paketi

Original `Shajara.zip` ochildi va ichidagi rasm to‘liq o‘qildi.

- Rasm: 32768 x 14079 px
- Megapixel: 461.3 MP
- Aniqlangan yirik node/kataklar: 515 ta

## Fayllar
- `data/shajara_numbered_map_v3.jpg` — barcha node raqamlangan umumiy xarita.
- `data/shajara_tiles_v3/` — rasm 12 ta katta bo‘lakka ajratilgan. Ismlarni shu bo‘laklarda yaqinlashtirib o‘qing.
- `data/shajara_verified_nodes_v3.csv` — bazaga yuklash uchun asosiy CSV.
- `data/shajara_verified_relations_v3.csv` — murakkab bog‘lanishlar uchun bo‘sh shablon.
- `data/shajara_spouse_candidates_v3.csv` — yonma-yon turgan node juftliklari bo‘yicha yordamchi taxminlar. Avtomatik import qilinmaydi.

## CSV to‘ldirish
`shajara_verified_nodes_v3.csv` da quyilarni to‘ldiring:

- `full_name` — shaxs ismi.
- `gender` — erkak yoki ayol.
- `father_node_id` — otasi node raqami, masalan `N001`.
- `mother_node_id` — onasi node raqami.
- `spouse_node_ids` — turmush o‘rtoqlari; bir nechta bo‘lsa `N010;N025`.
- `confirmed` — tekshirilgan bo‘lsa `1`.

## Import qilish
```bash
python manage.py migrate
python manage.py import_original_shajara_csv --nodes data/shajara_verified_nodes_v3.csv --dry-run
python manage.py import_original_shajara_csv --nodes data/shajara_verified_nodes_v3.csv --clear
```

Faqat test uchun hamma node’ni placeholder sifatida yuklash:
```bash
python manage.py import_original_shajara_csv --nodes data/shajara_verified_nodes_v3.csv --allow-unconfirmed --clear
```

Real shajara uchun `confirmed=1` bilan ishlang. Bu ota-ona/farzand aloqasi adashib ketmasligi uchun qo‘yilgan himoya.
