# Import xatosi tuzatildi

Agar import paytida quyidagi xato chiqsa:

```text
ValidationError: {'slug': ['Harflar, raqamlar, pastki chiziqlar yoki chiziqlardan iborat to'g'ri "slug" ni kiriting.']}
```

sababi Cyrillic ism slug maydoniga avtomatik tushib, Django `SlugField` validatsiyasidan o'tmay qolgan.

Bu paketda tuzatildi:

- `import_original_shajara_csv.py` har bir import qilingan shaxsga ASCII slug beradi: `node-n001`, `node-n002`, ...
- `models.py` ham Cyrillic ismda bo'sh slug yaratmaydigan qilib xavfsizlandi.
- `--allow-placeholder` argumenti ham qo'shildi, eski ko'rsatmalar bilan mos ishlaydi.

Import:

```bash
python manage.py migrate
python manage.py import_original_shajara_csv --nodes data/shajara_nodes_v4_names_missing_ready.csv --clear
```

Tekshirish:

```bash
python manage.py shell
```

```python
from genealogy.models import Person, Marriage, ParentChild
Person.objects.count()
Marriage.objects.count()
ParentChild.objects.count()
```
