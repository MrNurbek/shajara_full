from __future__ import annotations

import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils.text import slugify


class Gender(models.TextChoices):
    MALE = "M", "Erkak"
    FEMALE = "F", "Ayol"
    UNKNOWN = "U", "Noma’lum"


class ParentType(models.TextChoices):
    BIOLOGICAL = "BIO", "Biologik"
    ADOPTIVE = "ADP", "Asrab olingan"
    STEP = "STP", "O‘gay"
    GUARDIAN = "GRD", "Vasiy"
    UNKNOWN = "UNK", "Noma’lum"


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.CharField("Davlat", max_length=120, blank=True)
    region = models.CharField("Viloyat / hudud", max_length=120, blank=True)
    district = models.CharField("Tuman", max_length=120, blank=True)
    city = models.CharField("Shahar / qishloq", max_length=120, blank=True)
    street = models.CharField("Ko‘cha", max_length=200, blank=True)
    house = models.CharField("Uy", max_length=50, blank=True)
    postal_code = models.CharField("Pochta indeksi", max_length=20, blank=True)
    description = models.CharField("Izoh", max_length=255, blank=True)

    class Meta:
        verbose_name = "Manzil"
        verbose_name_plural = "Manzillar"
        ordering = ["country", "region", "district", "city", "street"]

    def __str__(self) -> str:
        parts = [self.country, self.region, self.district, self.city, self.street, self.house]
        return ", ".join(part for part in parts if part) or "Manzil"


class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField("Slug", max_length=180, unique=True, blank=True, db_index=True)

    first_name = models.CharField("Ism", max_length=120)
    last_name = models.CharField("Familiya", max_length=120, blank=True)
    middle_name = models.CharField("Otasining ismi", max_length=120, blank=True)
    full_name_custom = models.CharField("To‘liq ism", max_length=255, blank=True)

    gender = models.CharField("Jinsi", max_length=1, choices=Gender.choices, default=Gender.UNKNOWN)
    birth_date = models.DateField("Tug‘ilgan sana", null=True, blank=True)
    death_date = models.DateField("Vafot etgan sana", null=True, blank=True)
    birth_place = models.CharField("Tug‘ilgan joy", max_length=255, blank=True)
    death_place = models.CharField("Vafot etgan joy", max_length=255, blank=True)

    occupation = models.CharField("Kasbi", max_length=200, blank=True)
    biography = models.TextField("Biografiya", blank=True)
    addresses = models.ManyToManyField(Address, blank=True, related_name="residents", verbose_name="Manzillar")
    primary_photo = models.ImageField("Asosiy rasm", upload_to="people/primary/%Y/%m/", blank=True)

    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan vaqt", auto_now=True)

    class Meta:
        verbose_name = "Shaxs"
        verbose_name_plural = "Shaxslar"
        ordering = ["last_name", "first_name", "middle_name"]
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["birth_date"]),
        ]

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        if self.full_name_custom:
            return self.full_name_custom.strip()
        parts = [self.last_name, self.first_name, self.middle_name]
        value = " ".join(part for part in parts if part).strip()
        return value or f"Shaxs {self.pk}"

    @property
    def is_deceased(self) -> bool:
        return bool(self.death_date)

    @property
    def birth_year(self) -> int | None:
        return self.birth_date.year if self.birth_date else None

    @property
    def death_year(self) -> int | None:
        return self.death_date.year if self.death_date else None

    def clean(self) -> None:
        if self.birth_date and self.death_date and self.death_date < self.birth_date:
            raise ValidationError({"death_date": "Vafot sanasi tug‘ilgan sanadan oldin bo‘lishi mumkin emas."})

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            base = slugify(self.display_name, allow_unicode=False)[:150] or str(self.id)[:8]
            candidate = base
            index = 2
            while Person.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{index}"
                index += 1
            self.slug = candidate
        self.full_clean(exclude=None)
        super().save(*args, **kwargs)


class Photo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="photos", verbose_name="Shaxs")
    image = models.ImageField("Rasm", upload_to="people/photos/%Y/%m/")
    caption = models.CharField("Sarlavha", max_length=200, blank=True)
    taken_at = models.DateField("Olingan sana", null=True, blank=True)
    is_public = models.BooleanField("Ommaviy ko‘rinsin", default=True)
    order_index = models.PositiveIntegerField("Tartib", default=0)
    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)

    class Meta:
        verbose_name = "Rasm"
        verbose_name_plural = "Rasmlar"
        ordering = ["order_index", "taken_at", "id"]

    def __str__(self) -> str:
        return f"{self.person.display_name} — {self.caption or self.image.name}"


class Marriage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    spouse1 = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="marriages_as_spouse1", verbose_name="Turmush o‘rtoq 1")
    spouse2 = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="marriages_as_spouse2", verbose_name="Turmush o‘rtoq 2")
    start_date = models.DateField("Nikoh boshlangan sana", null=True, blank=True)
    end_date = models.DateField("Nikoh tugagan sana", null=True, blank=True)
    location_text = models.CharField("Joy", max_length=200, blank=True)
    notes = models.TextField("Izoh", blank=True)
    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)

    class Meta:
        verbose_name = "Nikoh"
        verbose_name_plural = "Nikohlar"
        ordering = ["start_date", "id"]
        constraints = [
            models.CheckConstraint(condition=~Q(spouse1=F("spouse2")), name="marriage_spouses_must_differ"),
            models.UniqueConstraint(fields=["spouse1", "spouse2"], name="uniq_canonical_marriage_pair"),
        ]

    def clean(self) -> None:
        if self.spouse1_id and self.spouse2_id and self.spouse1_id == self.spouse2_id:
            raise ValidationError("Bir shaxs o‘zi bilan nikoh bog‘lay olmaydi.")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "Nikoh tugash sanasi boshlanish sanasidan oldin bo‘lishi mumkin emas."})

    def save(self, *args, **kwargs) -> None:
        if self.spouse1_id and self.spouse2_id and str(self.spouse2_id) < str(self.spouse1_id):
            self.spouse1_id, self.spouse2_id = self.spouse2_id, self.spouse1_id
        self.full_clean(exclude=None)
        super().save(*args, **kwargs)

    @property
    def partners(self) -> tuple[Person, Person]:
        return self.spouse1, self.spouse2

    def other_partner(self, person: Person) -> Person | None:
        if self.spouse1_id == person.id:
            return self.spouse2
        if self.spouse2_id == person.id:
            return self.spouse1
        return None

    def __str__(self) -> str:
        return f"{self.spouse1.display_name} ⇄ {self.spouse2.display_name}"


class ParentChild(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    child = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="parent_links", verbose_name="Farzand")
    marriage = models.ForeignKey(Marriage, null=True, blank=True, on_delete=models.CASCADE, related_name="child_links", verbose_name="Nikoh orqali")
    parent = models.ForeignKey(Person, null=True, blank=True, on_delete=models.CASCADE, related_name="single_child_links", verbose_name="Yolg‘iz ota/ona")
    relation_type = models.CharField("Qarindoshlik turi", max_length=3, choices=ParentType.choices, default=ParentType.BIOLOGICAL)
    notes = models.CharField("Izoh", max_length=255, blank=True)
    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)

    class Meta:
        verbose_name = "Ota-ona — farzand bog‘lanishi"
        verbose_name_plural = "Ota-ona — farzand bog‘lanishlari"
        indexes = [
            models.Index(fields=["child"]),
            models.Index(fields=["marriage"]),
            models.Index(fields=["parent"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(Q(marriage__isnull=False) & Q(parent__isnull=True))
                | (Q(marriage__isnull=True) & Q(parent__isnull=False)),
                name="parent_child_exactly_one_parent_source",
            ),
            models.UniqueConstraint(fields=["child", "marriage"], condition=Q(marriage__isnull=False), name="uniq_child_per_marriage"),
            models.UniqueConstraint(fields=["child", "parent"], condition=Q(parent__isnull=False), name="uniq_child_per_single_parent"),
        ]

    def clean(self) -> None:
        if bool(self.marriage_id) == bool(self.parent_id):
            raise ValidationError("Farzand bog‘lanishi nikoh yoki yolg‘iz ota/ona orqali bo‘lishi kerak; ikkalasi bir vaqtda emas.")
        if self.parent_id and self.child_id and self.parent_id == self.child_id:
            raise ValidationError("Shaxs o‘zi o‘ziga ota/ona bo‘la olmaydi.")
        if self.marriage_id and self.child_id:
            spouse_ids = {self.marriage.spouse1_id, self.marriage.spouse2_id}
            if self.child_id in spouse_ids:
                raise ValidationError("Nikohdagi shaxs o‘sha nikohning farzandi sifatida belgilanmaydi.")

    def save(self, *args, **kwargs) -> None:
        self.full_clean(exclude=None)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        source = self.marriage or self.parent
        return f"{self.child.display_name} ← {source}"
