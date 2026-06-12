from __future__ import annotations

import csv
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_date
from django.utils.text import slugify

from genealogy.models import Gender, Person, ParentChild
from genealogy.services.family_ops import add_child, ensure_marriage


def norm(value):
    return (value or "").strip()


def norm_gender(value):
    value = norm(value).lower()
    if value in {"m", "male", "erkak", "эркак", "e", "1"}:
        return Gender.MALE
    if value in {"f", "female", "ayol", "аёл", "a", "2"}:
        return Gender.FEMALE
    return Gender.UNKNOWN


def date_from_year(value):
    value = norm(value)
    if not value:
        return None
    # 1880, 1880.0, 1880-yil kabi qiymatlarni ham qabul qiladi.
    match = re.search(r"\d{3,4}", value)
    if not match:
        return None
    year = int(match.group(0))
    if year < 1 or year > 9999:
        return None
    return f"{year:04d}-01-01"


def truthy(value):
    return norm(value).lower() in {"1", "true", "yes", "ha", "xa", "ok", "y"}


def safe_slug(node_id, name):
    """Django SlugField ASCII validatsiyasidan o‘tadigan slug yaratadi.

    Cyrillic ismlardan slugify(..., allow_unicode=True) qilinganda eski modelda
    ValidationError chiqadi. Shuning uchun importda doim ASCII slug beramiz.
    """
    node = norm(node_id)
    if node:
        base = f"node-{slugify(node, allow_unicode=False)}"
    else:
        base = slugify(name, allow_unicode=False)
    base = (base or "person")[:150].strip("-") or "person"
    candidate = base
    index = 2
    while Person.objects.filter(slug=candidate).exists():
        candidate = f"{base}-{index}"
        index += 1
    return candidate


class Command(BaseCommand):
    help = "Original shajara CSV faylini bazaga yuklaydi. Bo'sh ma'lumotlarni xavfsiz placeholder bilan import qiladi."

    def add_arguments(self, parser):
        parser.add_argument("--nodes", required=True, help="CSV fayl yo'li")
        parser.add_argument("--clear", action="store_true", help="Oldingi shajara ma'lumotlarini tozalab import qiladi")
        parser.add_argument("--dry-run", action="store_true", help="Bazaga yozmasdan tekshiradi")
        parser.add_argument("--allow-unconfirmed", action="store_true", help="confirmed=1 bo'lmagan qatorlarni ham import qiladi")
        parser.add_argument("--allow-placeholder", action="store_true", help="Moslik uchun qoldirilgan; V4 faylda placeholderlar allaqachon tayyor")

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["nodes"])
        if not path.exists():
            raise CommandError(f"CSV topilmadi: {path}")

        rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig", newline="")))
        selected = []
        for row in rows:
            confirmed = truthy(row.get("confirmed"))
            if not confirmed and not options["allow_unconfirmed"]:
                continue
            node_id = norm(row.get("node_id"))
            name = norm(row.get("full_name"))
            if not name:
                name = f"Ma'lumot yo'q ({node_id or 'ID yoq'})"
            row["_name"] = name
            row["_node_id"] = node_id
            selected.append(row)

        self.stdout.write(f"CSV qatorlari: {len(rows)}")
        self.stdout.write(f"Import qatorlari: {len(selected)}")

        if options["dry_run"]:
            for row in selected[:30]:
                self.stdout.write(f"{row.get('_node_id')} -> {row.get('_name')}")
            self.stdout.write(self.style.WARNING("DRY RUN: bazaga yozilmadi."))
            return

        if options["clear"]:
            from genealogy.models import Address, Marriage, Photo
            ParentChild.objects.all().delete()
            Marriage.objects.all().delete()
            Photo.objects.all().delete()
            Person.objects.all().delete()
            Address.objects.all().delete()

        node_to_person = {}
        for row in selected:
            name = row["_name"]
            parts = name.split()
            first = parts[0] if parts else name
            last = " ".join(parts[1:]) if len(parts) > 1 else ""
            birth_date = date_from_year(row.get("birth_year"))
            death_date = date_from_year(row.get("death_year"))
            node_id = row["_node_id"]

            person = Person.objects.create(
                slug=safe_slug(node_id, name),
                first_name=first[:120],
                last_name=last[:120],
                full_name_custom=name[:255],
                gender=norm_gender(row.get("gender")),
                birth_date=parse_date(birth_date) if birth_date else None,
                death_date=parse_date(death_date) if death_date else None,
                biography=f"Import node_id: {node_id}. Notes: {norm(row.get('notes'))}",
            )
            if node_id:
                node_to_person[node_id] = person

        marriages_created = 0
        for row in selected:
            person = node_to_person.get(row["_node_id"])
            spouse_values = norm(row.get("spouse_node_ids")).replace(",", ";").split(";")
            for spouse_node_id in [s.strip() for s in spouse_values if s.strip()]:
                spouse = node_to_person.get(spouse_node_id)
                if person and spouse and person.pk != spouse.pk:
                    ensure_marriage([person, spouse])
                    marriages_created += 1

        child_links_created = 0
        for row in selected:
            child = node_to_person.get(row["_node_id"])
            father = node_to_person.get(norm(row.get("father_node_id")))
            mother = node_to_person.get(norm(row.get("mother_node_id")))
            if not child:
                continue
            if father and mother:
                add_child(child, [father, mother])
                child_links_created += 1
            elif father:
                add_child(child, [father])
                child_links_created += 1
            elif mother:
                add_child(child, [mother])
                child_links_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Import tugadi: {len(node_to_person)} ta shaxs. "
            f"Nikoh urinishlari: {marriages_created}. Farzand bog'lanishlari: {child_links_created}."
        ))
