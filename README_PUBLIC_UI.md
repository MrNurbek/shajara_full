# Public UI yangilanishi

Bu versiyada oddiy foydalanuvchi admin panelga yo‘naltirilmaydi. `/tree/` sahifasidagi sidebar faqat ochiq ma’lumotlar, statistika, foydalanish tartibi va shajara bo‘limlarini ko‘rsatadi.

## Oddiy foydalanuvchi ko‘radigan qismlar

- Shajara daraxti
- Shaxs qidiruvi
- Shaxs profili modal oynasi
- Ochiq statistika
- Foydalanish bo‘yicha qisqa qo‘llanma
- Mobil bottom navigation

## Admin/staff foydalanuvchi

Agar foydalanuvchi staff bo‘lsa, qo‘shimcha boshqaruv tugmalari ko‘rinadi:

- `+ Shaxs`
- Profil ichida `Tahrirlash`
- `Farzand bog‘lash`
- `Turmush o‘rtoq qo‘shish`
- Sidebar ichida `Admin panel`

Oddiy foydalanuvchi bu tugmalarni ko‘rmaydi.

## Mobil ishlatish

Telefon ekranlari uchun:

- Sidebar ixcham yuqori panelga aylanadi.
- Pastda `Daraxt`, `Qidiruv`, `Statistika`, `Qo‘llanma` tezkor navigatsiyasi chiqadi.
- Daraxt pan/zoom uchun `touch-action:none` bilan moslashtirilgan.
- Modal oynalar 100dvh bo‘yicha scroll bilan ishlaydi.
