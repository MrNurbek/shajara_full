# Bazaga 100 ta ma’lumot qo‘shish

Loyihaga 2 xil usul qo‘shildi.

## 1-usul: avtomatik 100 ta demo shajara yaratish

```bash
python manage.py migrate
python manage.py seed_100 --clear
```

Natija:

- 100 ta shaxs;
- 10 ta asosiy oila;
- ota-ona, turmush o‘rtoq va farzand bog‘lanishlari;
- tug‘ilgan sana, kasb, manzil, biografiya.

Agar bazani butunlay tozalab, faqat 100 ta demo ma’lumot qoldirmoqchi bo‘lsangiz:

```bash
python manage.py seed_100 --clear-all
```

Diqqat: `--clear-all` barcha mavjud shajara ma’lumotlarini o‘chiradi.

## 2-usul: real 100 ta qarindosh ma’lumotini CSV orqali import qilish

Namuna fayl:

```text
data/sample_people_100.csv
```

Import:

```bash
python manage.py import_people_csv --file data/sample_people_100.csv
```

CSV ustunlari:

```text
first_name,last_name,middle_name,full_name_custom,gender,birth_date,death_date,birth_place,death_place,occupation,biography,father_full_name,mother_full_name,spouse_full_name,address_country,address_region,address_district,address_city
```

Sana formati:

```text
YYYY-MM-DD
```

Jins qiymatlari:

```text
M yoki Erkak
F yoki Ayol
U yoki Noma’lum
```

Aloqa bog‘lash qoidasi:

- `father_full_name` va `mother_full_name` CSVdagi `full_name_custom` qiymati bilan bir xil yozilishi kerak;
- `spouse_full_name` ham CSVdagi `full_name_custom` bilan bir xil bo‘lishi kerak;
- avval barcha shaxslar yaratiladi, keyin nikoh va ota-ona/farzand bog‘lanishlari ulanadi.
