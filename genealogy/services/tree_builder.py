from __future__ import annotations

from datetime import date
from typing import Any
from django.db.models import Q, QuerySet

from genealogy.models import Marriage, ParentChild, Person


def person_mini(person: Person) -> dict[str, Any]:
    return {
        "id": str(person.id),
        "name": person.display_name,
        "gender": person.gender,
        "birth_year": person.birth_year,
        "death_year": person.death_year,
        "is_deceased": person.is_deceased,
    }


def marriages_of(person: Person) -> QuerySet[Marriage]:
    return (
        Marriage.objects.filter(Q(spouse1=person) | Q(spouse2=person))
        .select_related("spouse1", "spouse2")
        .prefetch_related("child_links__child")
        .order_by("start_date", "id")
    )


def child_sort_key(person: Person) -> tuple[bool, date, str, str, str, str]:
    """Farzandlarni yosh tartibida saralaydi: 1-farzand eng katta bo‘ladi.

    Tug‘ilgan sanasi yo‘q farzandlar ism-familiyasi bo‘yicha oxirroqqa qo‘yiladi.
    Bu tartib SQLite/PostgreSQL dagi NULL saralash farqiga bog‘lanib qolmaydi.
    """
    birth_date = person.birth_date or date.max
    return (
        person.birth_date is None,
        birth_date,
        person.last_name.lower(),
        person.first_name.lower(),
        person.middle_name.lower(),
        str(person.id),
    )

def children_of_marriage(marriage: Marriage) -> list[Person]:
    children = [
        link.child
        for link in marriage.child_links.select_related("child").all()
    ]
    return sorted(children, key=child_sort_key)


def children_of_single_parent(parent: Person) -> list[Person]:
    children = [
        link.child
        for link in parent.single_child_links.select_related("child").all()
    ]
    return sorted(children, key=child_sort_key)


def order_partners(partners: list[Person]) -> list[Person]:
    def rank(person: Person) -> tuple[int, str]:
        gender_rank = 0 if person.gender == "M" else 1 if person.gender == "F" else 2
        return gender_rank, person.display_name.lower()

    return sorted(partners, key=rank)


def build_from_person(
    person: Person,
    *,
    seen_marriages: set[str] | None = None,
    person_path: set[str] | None = None,
    max_depth: int = 50,
) -> dict[str, Any]:
    if seen_marriages is None:
        seen_marriages = set()
    if person_path is None:
        person_path = set()

    pid = str(person.id)

    if max_depth <= 0:
        return {"type": "single", "person": person_mini(person), "children": [], "truncated": True}
    if pid in person_path:
        return {"type": "single", "person": person_mini(person), "children": [], "cycle": True}

    next_path = {*person_path, pid}

    # Nikohni asosiy tugun sifatida ko'rsatish (er va xotin yonma-yon)
    main_node: dict[str, Any] | None = None
    remaining_marriages: list[Marriage] = []

    all_marriages = list(marriages_of(person))
    for i, marriage in enumerate(all_marriages):
        if str(marriage.id) not in seen_marriages:
            main_node = build_from_marriage(
                marriage,
                seen_marriages=seen_marriages,
                person_path=next_path,
                max_depth=max_depth - 1,
            )
            remaining_marriages = all_marriages[i + 1:]
            break

    if main_node is None:
        # Nikohi yo'q yoki hammasi ko'rilgan — yakka tugun
        node: dict[str, Any] = {"type": "single", "person": person_mini(person), "children": []}
        for birth_order, child in enumerate(children_of_single_parent(person), start=1):
            child_node = build_from_person(
                child,
                seen_marriages=seen_marriages,
                person_path=next_path,
                max_depth=max_depth - 1,
            )
            child_node["birth_order"] = birth_order
            node["children"].append(child_node)
        return node

    # Qolgan nikohlarni farzand sifatida qo'shish
    for marriage in remaining_marriages:
        marriage_node = build_from_marriage(
            marriage,
            seen_marriages=seen_marriages,
            person_path=next_path,
            max_depth=max_depth - 1,
        )
        if marriage_node:
            main_node["children"].append(marriage_node)

    # Yakka ota/onadan tug'ilgan farzandlarni qo'shish
    for child in children_of_single_parent(person):
        child_node = build_from_person(
            child,
            seen_marriages=seen_marriages,
            person_path=next_path,
            max_depth=max_depth - 1,
        )
        main_node["children"].append(child_node)

    return main_node


def build_from_marriage(
    marriage: Marriage,
    *,
    seen_marriages: set[str] | None = None,
    person_path: set[str] | None = None,
    max_depth: int = 50,
) -> dict[str, Any] | None:
    if seen_marriages is None:
        seen_marriages = set()
    if person_path is None:
        person_path = set()

    mid = str(marriage.id)
    if mid in seen_marriages:
        return None
    seen_marriages.add(mid)

    partners = order_partners([marriage.spouse1, marriage.spouse2])
    node: dict[str, Any] = {
        "type": "union",
        "id": mid,
        "partners": [person_mini(partner) for partner in partners],
        "children": [],
    }

    if max_depth <= 0:
        node["truncated"] = True
        return node

    next_path = {*person_path, *(str(partner.id) for partner in partners)}
    for birth_order, child in enumerate(children_of_marriage(marriage), start=1):
        child_node = build_from_person(
            child,
            seen_marriages=seen_marriages,
            person_path=next_path,
            max_depth=max_depth - 1,
        )
        child_node["birth_order"] = birth_order
        node["children"].append(child_node)
    return node


def root_people() -> QuerySet[Person]:
    child_ids = set(ParentChild.objects.values_list("child_id", flat=True))

    # Ota-onasi yo‘q, lekin asosiy shajara ichidagi farzand bilan turmush qurgan
    # shaxslar alohida root bo‘lmasligi kerak.
    external_spouse_ids = set()

    for spouse1_id, spouse2_id in Marriage.objects.values_list("spouse1_id", "spouse2_id"):
        spouse1_is_child = spouse1_id in child_ids
        spouse2_is_child = spouse2_id in child_ids

        if spouse1_is_child and not spouse2_is_child:
            external_spouse_ids.add(spouse2_id)

        elif spouse2_is_child and not spouse1_is_child:
            external_spouse_ids.add(spouse1_id)

    excluded_ids = child_ids | external_spouse_ids

    return (
        Person.objects
        .exclude(id__in=excluded_ids)
        .order_by("last_name", "first_name", "middle_name")
    )


def build_forest_all_roots(max_depth: int = 50) -> dict[str, Any]:
    seen_marriages: set[str] = set()
    forest_children: list[dict[str, Any]] = []

    for person in root_people():
        person_marriages = list(marriages_of(person))
        if person_marriages:
            for marriage in person_marriages:
                node = build_from_marriage(marriage, seen_marriages=seen_marriages, max_depth=max_depth)
                if node:
                    forest_children.append(node)
        else:
            forest_children.append(build_from_person(person, seen_marriages=seen_marriages, max_depth=max_depth))

    return {"type": "root", "children": forest_children}
