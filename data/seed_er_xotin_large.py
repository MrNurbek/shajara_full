#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Katta test shajara import scripti.
Ishlatish:
    python seed_er_xotin_large.py --clear-test

Bu script faqat [TEST-ERXOTIN-LARGE] belgisi bilan yaratilgan eski test yozuvlarini tozalaydi.
Real bazadagi boshqa shaxslar saqlanadi.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

try:
    import django
    django.setup()
except Exception as exc:
    print("Django sozlamalarini yuklashda xato:", exc)
    print("Scriptni manage.py joylashgan loyiha root papkasidan ishga tushiring.")
    sys.exit(1)

from django.db import transaction
from genealogy.models import Marriage, ParentChild, Person

TAG = "[TEST-ERXOTIN-LARGE]"
BASE_DIR = Path(__file__).resolve().parent
NODES_FILE = BASE_DIR / "data" / "er_xotin_large_nodes.csv"
RELATIONS_FILE = BASE_DIR / "data" / "er_xotin_large_relations.csv"


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Fayl topilmadi: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def clean_test_data() -> None:
    test_people = Person.objects.filter(biography__contains=TAG)
    test_ids = list(test_people.values_list("id", flat=True))
    if test_ids:
        ParentChild.objects.filter(child_id__in=test_ids).delete()
        ParentChild.objects.filter(parent_id__in=test_ids).delete()
        Marriage.objects.filter(spouse1_id__in=test_ids).delete()
        Marriage.objects.filter(spouse2_id__in=test_ids).delete()
        test_people.delete()


def import_data() -> tuple[int, int, int]:
    nodes = read_csv(NODES_FILE)
    relations = read_csv(RELATIONS_FILE)
    node_to_person: dict[str, Person] = {}

    for row in nodes:
        person = Person(
            id=row["uuid"],
            first_name=row["first_name"] or row["full_name"],
            last_name=row["last_name"] or "",
            middle_name=row["middle_name"] or "",
            full_name_custom=row["full_name"] or "",
            gender=row["gender"] or "U",
            birth_date=row["birth_date"] or None,
            death_date=row["death_date"] or None,
            birth_place=row["birth_place"] or "",
            occupation=row["occupation"] or "",
            biography=row["biography"] or TAG,
        )
        person.save()
        node_to_person[row["node_id"]] = person

    marriage_by_id: dict[str, Marriage] = {}
    for row in relations:
        if row["relation_type"] != "marriage":
            continue
        p1 = node_to_person[row["person1_node_id"]]
        p2 = node_to_person[row["person2_node_id"]]
        marriage = Marriage(
            spouse1=p1,
            spouse2=p2,
            start_date=row["start_date"] or None,
            location_text=row["location_text"] or "",
            notes=row["notes"] or TAG,
        )
        marriage.save()
        marriage_by_id[row["marriage_id"]] = marriage

    child_count = 0
    for row in relations:
        if row["relation_type"] != "parent_child":
            continue
        child = node_to_person[row["child_node_id"]]
        marriage = marriage_by_id[row["marriage_id"]]
        ParentChild.objects.create(child=child, marriage=marriage, relation_type="BIO", notes=row["notes"] or TAG)
        child_count += 1
    return len(node_to_person), len(marriage_by_id), child_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear-test", action="store_true", help="Avval shu test datasetini tozalaydi.")
    args = parser.parse_args()
    with transaction.atomic():
        if args.clear_test:
            clean_test_data()
        people_count, marriage_count, child_count = import_data()
    print("Import tugadi.")
    print(f"Shaxslar: {people_count}")
    print(f"Nikohlar: {marriage_count}")
    print(f"Farzand boglanishlari: {child_count}")
    print("Tekshirish: /tree/ sahifasini oching.")

if __name__ == "__main__":
    main()
