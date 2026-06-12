# Shajara import V4 — bo‘sh ma’lumotlar bilan xavfsiz yuklash

Bu paketda rasmda aniqlangan 515 ta node bazaga tushadigan qilib tayyorlandi.

Asosiy fayl:

```text
data/shajara_nodes_v4_names_missing_ready.csv
```

Qanday ishlaydi:

- Agar rasmda ism aniq o‘qilgan bo‘lsa, `full_name` ustuniga ism kiritildi.
- Agar ism/familiya/xotini/ota-onasi yoki boshqa ma’lumot rasmda ko‘rsatilmagan yoki aniq o‘qilmagan bo‘lsa, `Ma'lumot yo'q (Nxxx)` shaklida kiritildi.
- `confirmed=1` barcha qatorlarga qo‘yildi, shuning uchun import qilinganda 515 ta node bazaga tushadi.
- `father_node_id`, `mother_node_id`, `spouse_node_ids` faqat ishonchli aniqlangan joylarda to‘ldiriladi. Noto‘g‘ri avlod bog‘lanmasligi uchun taxminiy aloqalar kiritilmadi.

Muhim: bu fayl shajarani buzmaslik uchun noma’lum ota-ona/xotin aloqalarini bo‘sh qoldiradi. Keyin siz xaritaga qarab `father_node_id`, `mother_node_id`, `spouse_node_ids` ustunlarini bosqichma-bosqich to‘ldirasiz.

## Yuklash

```bash
python manage.py migrate
python manage.py import_original_shajara_csv --nodes data/shajara_nodes_v4_names_missing_ready.csv --clear
```

Yoki eski nomdagi faylni ishlatmoqchi bo‘lsangiz, paket ichida `data/shajara_verified_nodes_v3.csv` ham shu V4 formatga almashtirilgan:

```bash
python manage.py import_original_shajara_csv --nodes data/shajara_verified_nodes_v3.csv --clear
```

## Tekshirish

```bash
python manage.py shell
```

```python
from genealogy.models import Person, Marriage, ParentChild
Person.objects.count()
Marriage.objects.count()
ParentChild.objects.count()
```

Kutiladigan natija: `Person.objects.count()` 515 atrofida bo‘ladi.

## Bog‘lanishlarni to‘ldirish qoidasi

Misol:

```csv
node_id,full_name,father_node_id,mother_node_id,spouse_node_ids,confirmed
N001,ОМОНКЕЛДИ,,,,1
N002,АЛИМАРДОН,N001,,,1
N003,РАСУЛБЕРДИ,N002,,,1
```

Er-xotin uchun:

```csv
N010,ЯЗДОНҚУЛ,,,,N011,1
N011,Ҳадича,,,,N010,1
```

Bir nechta xotin yoki er bo‘lsa:

```csv
N010;N025
```

## Nega hamma ota-ona avtomatik bog‘lanmadi?

Rasmda ko‘plab chiziqlar uzun, ustma-ust va juda kichik. Taxminiy bog‘lash genealogik bazani buzishi mumkin. Shuning uchun ishonchsiz aloqalar bo‘sh qoldirildi, lekin barcha node bazaga kiritiladigan qilib tayyorlandi.