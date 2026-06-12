# Fullscreen / xaritani kattalashtirish yangilanishi

Ushbu versiyada `/tree/` sahifasiga shajara xaritasini kattalashtirish uchun tugmalar qayta qo'shildi:

- yuqori toolbar ichida: `⛶ Xaritani kattalashtirish`
- shajara xaritasi sarlavhasida: `⛶ To'liq ekran`

Tugmalar browserning native Fullscreen API'sidan foydalanadi. Agar browser fullscreenni bloklasa yoki qo'llamasa, fallback rejim ishlaydi: xarita butun oynani egallaydi. `Esc` bilan chiqish mumkin.

Tekshirildi:

```bash
python manage.py check
```

Natija: `System check identified no issues`.
