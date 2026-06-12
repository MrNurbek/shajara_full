# Shajara 2 — mukammallashtirilgan Django loyiha

Bu loyiha oilaviy genealogik shajarani yaratish, ko‘rish, qidirish va boshqarish uchun tayyorlangan Django + Django REST Framework asosidagi web ilovadir.

## Asosiy imkoniyatlar

- Interaktiv shajara sahifasi: `/tree/`
- Pan, drag, zoom, fit-to-screen boshqaruvlari
- Ism, familiya, otasining ismi, kasb bo‘yicha qidiruv
- Shaxs profili modal oynada AJAX orqali ochiladi
- Profil ichida: biografiya, ota-ona, turmush o‘rtoq, farzandlar, manzillar, galereya
- Rasm lightbox ko‘rinishida kattalashtirib ochiladi
- Staff foydalanuvchi uchun frontenddan shaxs qo‘shish, tahrirlash, nikoh qo‘shish, farzand bog‘lash
- Admin panel orqali kengaytirilgan boshqaruv
- Nikoh juftligini kanonik saqlash: `(A, B)` va `(B, A)` takrorlanmaydi
- Farzand bog‘lanishida XOR cheklovi: yoki nikoh orqali, yoki yolg‘iz ota/ona orqali
- `.env` orqali sozlanadigan production-aware settings
- SQLite yoki PostgreSQL bilan ishlash
- Docker va docker compose konfiguratsiyasi
- Demo ma’lumot yaratish komandasi
- Testlar

## Lokal ishga tushirish

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/Mac:

```bash
source .venv/bin/activate
```

Kutubxonalarni o‘rnating:

```bash
pip install -r requirements.txt
```

`.env.example` faylini `.env` qilib nusxalang:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
copy .env.example .env
```

Migratsiya va demo ma’lumot:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

Brauzerda oching:

```text
http://127.0.0.1:8000/tree/
```

Admin panel:

```text
http://127.0.0.1:8000/admin/
```

## Docker orqali ishga tushirish

`.env` faylida PostgreSQL URL ochiq bo‘lsin:

```env
DATABASE_URL=postgresql://shajara:strong_password@db:5432/shajara
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com
```

Keyin:

```bash
docker compose up --build
```

## Test

```bash
python manage.py test
```

## Muhim izoh

Frontenddan qo‘shish/tahrirlash API’lari faqat `is_staff=True` foydalanuvchi uchun ishlaydi. Oddiy foydalanuvchilar shajarani ko‘ra oladi, lekin ma’lumotni o‘zgartira olmaydi.
