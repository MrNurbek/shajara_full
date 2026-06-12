# CreateUsers tuzatilgan versiya

Bu paketda `/createusers/` alohida superuser-only boshqaruv paneli sifatida ishlaydi. Django admin ishlatilmaydi.

## Asosiy URLlar

- `/createusers/login/` — superuser login
- `/createusers/` — shaxslar jadvali va qidiruv
- `/createusers/person/create/` — yangi shaxs
- `/createusers/person/<uuid>/` — shaxs profili
- `/createusers/person/<uuid>/spouse/add/` — er/xotin qo‘shish
- `/createusers/person/<uuid>/child/add/` — farzand qo‘shish

## Ishga tushirish

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Brauzerda:

```text
http://127.0.0.1:8000/createusers/
```

Agar data import kerak bo‘lsa:

```powershell
python manage.py import_original_shajara_csv --nodes data/shajara_nodes_v4_names_missing_ready.csv --clear
```
