from __future__ import annotations

from collections.abc import Sequence
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from genealogy.models import Marriage, ParentChild, ParentType, Person


def normalize_two_people(people: Sequence[Person]) -> tuple[Person, Person]:
    unique: list[Person] = []
    seen: set[str] = set()
    for person in people:
        if not isinstance(person, Person):
            raise ValidationError("Faqat Person obyektlari qabul qilinadi.")
        key = str(person.pk)
        if key in seen:
            continue
        seen.add(key)
        unique.append(person)
    if len(unique) != 2:
        raise ValidationError("Nikoh uchun aynan 2 ta turli shaxs kerak.")
    return unique[0], unique[1]


def canonical_pair(p1: Person, p2: Person) -> tuple[Person, Person]:
    if p1.pk == p2.pk:
        raise ValidationError("Bir shaxs o‘zi bilan nikoh bog‘lay olmaydi.")
    return (p1, p2) if str(p1.pk) < str(p2.pk) else (p2, p1)


@transaction.atomic
def ensure_marriage(
    partners: Sequence[Person],
    *,
    start_date=None,
    end_date=None,
    location_text: str = "",
    notes: str = "",
) -> Marriage:
    p1, p2 = normalize_two_people(partners)
    spouse1, spouse2 = canonical_pair(p1, p2)

    marriage, created = Marriage.objects.get_or_create(
        spouse1=spouse1,
        spouse2=spouse2,
        defaults={
            "start_date": start_date,
            "end_date": end_date,
            "location_text": location_text or "",
            "notes": notes or "",
        },
    )
    if not created:
        changed = False
        if start_date and not marriage.start_date:
            marriage.start_date = start_date
            changed = True
        if end_date and not marriage.end_date:
            marriage.end_date = end_date
            changed = True
        if location_text and not marriage.location_text:
            marriage.location_text = location_text
            changed = True
        if notes:
            marriage.notes = f"{marriage.notes}\n{notes}".strip()
            changed = True
        if changed:
            marriage.save()
    return marriage


@transaction.atomic
def add_child(
    child: Person,
    parents: Sequence[Person] | Marriage,
    relation_type: str = ParentType.BIOLOGICAL,
    notes: str = "",
) -> ParentChild:
    if not isinstance(child, Person):
        raise ValidationError("Farzand Person obyektida bo‘lishi kerak.")

    try:
        if isinstance(parents, Marriage):
            if child.pk in {parents.spouse1_id, parents.spouse2_id}:
                raise ValidationError("Nikohdagi shaxs o‘sha nikohning farzandi sifatida belgilanmaydi.")
            obj, _ = ParentChild.objects.get_or_create(
                child=child,
                marriage=parents,
                defaults={"relation_type": relation_type, "notes": notes or ""},
            )
            return obj

        parent_list = list(parents)
        if len(parent_list) == 1:
            parent = parent_list[0]
            if parent.pk == child.pk:
                raise ValidationError("Shaxs o‘zi o‘ziga ota/ona bo‘la olmaydi.")
            obj, _ = ParentChild.objects.get_or_create(
                child=child,
                parent=parent,
                defaults={"relation_type": relation_type, "notes": notes or ""},
            )
            return obj

        if len(parent_list) == 2:
            if child.pk in {parent_list[0].pk, parent_list[1].pk}:
                raise ValidationError("Farzand ota-onalardan biri bilan bir xil bo‘lishi mumkin emas.")
            marriage = ensure_marriage(parent_list)
            obj, _ = ParentChild.objects.get_or_create(
                child=child,
                marriage=marriage,
                defaults={"relation_type": relation_type, "notes": notes or ""},
            )
            return obj
    except IntegrityError as exc:
        raise ValidationError("Bu farzand bog‘lanishi avval yaratilgan yoki model chekloviga zid.") from exc

    raise ValidationError("Ota-ona sifatida 1 ta shaxs, 2 ta shaxs yoki Marriage obyektini yuboring.")
