from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from genealogy.models import Address, Gender, Person
from genealogy.services.family_ops import add_child, ensure_marriage


def parse_date(value: str):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise CommandError(f"Sana formati noto‘g‘ri: {value}. Format: YYYY-MM-DD")


def normalize_gender(value: str) -> str:
    value = (value or "").strip().lower()
    if value in {"m", "male", "erkak", "e"}:
        return Gender.MALE
    if value in {"f", "female", "ayol", "a"}:
        return Gender.FEMALE
    return Gender.UNKNOWN


class Command(BaseCommand):
    help = "CSV fayldan shaxslarni import qiladi va ota-ona/turmush o‘rtoq aloqalarini bog‘laydi."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="CSV fayl manzili. Masalan: data/sample_people_100.csv")
        parser.add_argument("--encoding", default="utf-8-sig", help="CSV encoding. Standart: utf-8-sig")
        parser.add_argument("--delimiter", default=",", help="CSV ajratgich. Standart: vergul")

    @transaction.atomic
    def handle(self, *args, **options):
        csv_path = Path(options["file"])
        if not csv_path.exists():
            raise CommandError(f"CSV fayl topilmadi: {csv_path}")

        with csv_path.open("r", encoding=options["encoding"], newline="") as file_obj:
            rows = list(csv.DictReader(file_obj, delimiter=options["delimiter"]))

        if not rows:
            raise CommandError("CSV fayl bo‘sh.")

        people_by_key: dict[str, Person] = {}
        created_count = 0
        updated_count = 0

        for row in rows:
            first_name = (row.get("first_name") or "").strip()
            last_name = (row.get("last_name") or "").strip()
            middle_name = (row.get("middle_name") or "").strip()
            full_name_custom = (row.get("full_name_custom") or "").strip()
            key = full_name_custom or " ".join(part for part in [last_name, first_name, middle_name] if part)
            if not first_name and not full_name_custom:
                raise CommandError("Har bir qatorda kamida first_name yoki full_name_custom bo‘lishi kerak.")

            country = (row.get("address_country") or "O‘zbekiston").strip()
            region = (row.get("address_region") or "").strip()
            district = (row.get("address_district") or "").strip()
            city = (row.get("address_city") or "").strip()
            address = None
            if region or district or city:
                address, _ = Address.objects.get_or_create(
                    country=country,
                    region=region,
                    district=district,
                    city=city,
                )

            defaults = {
                "first_name": first_name or full_name_custom,
                "last_name": last_name,
                "middle_name": middle_name,
                "gender": normalize_gender(row.get("gender") or ""),
                "birth_date": parse_date(row.get("birth_date") or ""),
                "death_date": parse_date(row.get("death_date") or ""),
                "birth_place": (row.get("birth_place") or "").strip(),
                "death_place": (row.get("death_place") or "").strip(),
                "occupation": (row.get("occupation") or "").strip(),
                "biography": (row.get("biography") or "").strip(),
            }

            person, created = Person.objects.update_or_create(
                full_name_custom=key,
                defaults=defaults,
            )
            if address:
                person.addresses.add(address)
            people_by_key[key] = person
            if created:
                created_count += 1
            else:
                updated_count += 1

        marriage_count = 0
        parent_link_count = 0
        for row in rows:
            full_name_custom = (row.get("full_name_custom") or "").strip()
            first_name = (row.get("first_name") or "").strip()
            last_name = (row.get("last_name") or "").strip()
            middle_name = (row.get("middle_name") or "").strip()
            key = full_name_custom or " ".join(part for part in [last_name, first_name, middle_name] if part)
            person = people_by_key[key]

            spouse_key = (row.get("spouse_full_name") or "").strip()
            if spouse_key and spouse_key in people_by_key:
                ensure_marriage([person, people_by_key[spouse_key]])
                marriage_count += 1

            father_key = (row.get("father_full_name") or "").strip()
            mother_key = (row.get("mother_full_name") or "").strip()
            father = people_by_key.get(father_key) if father_key else None
            mother = people_by_key.get(mother_key) if mother_key else None
            if father and mother:
                add_child(person, [father, mother])
                parent_link_count += 1
            elif father:
                add_child(person, [father])
                parent_link_count += 1
            elif mother:
                add_child(person, [mother])
                parent_link_count += 1

        self.stdout.write(self.style.SUCCESS(f"Import tugadi. Yangi: {created_count}, yangilangan: {updated_count}."))
        self.stdout.write(self.style.SUCCESS(f"Nikoh bog‘lash urinishlari: {marriage_count}, ota-ona/farzand bog‘lanishlari: {parent_link_count}."))
