from __future__ import annotations

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


def children_of_marriage(marriage: Marriage) -> list[Person]:
    return [
        link.child
        for link in marriage.child_links.select_related("child").order_by(
            "child__birth_date", "child__last_name", "child__first_name"
        )
    ]


def children_of_single_parent(parent: Person) -> list[Person]:
    return [
        link.child
        for link in parent.single_child_links.select_related("child").order_by(
            "child__birth_date", "child__last_name", "child__first_name"
        )
    ]


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
    node: dict[str, Any] = {"type": "single", "person": person_mini(person), "children": []}

    if max_depth <= 0:
        node["truncated"] = True
        return node
    if pid in person_path:
        node["cycle"] = True
        return node

    next_path = {*person_path, pid}

    for marriage in marriages_of(person):
        marriage_node = build_from_marriage(
            marriage,
            seen_marriages=seen_marriages,
            person_path=next_path,
            max_depth=max_depth - 1,
        )
        if marriage_node:
            node["children"].append(marriage_node)

    for child in children_of_single_parent(person):
        node["children"].append(
            build_from_person(
                child,
                seen_marriages=seen_marriages,
                person_path=next_path,
                max_depth=max_depth - 1,
            )
        )

    return node


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
    for child in children_of_marriage(marriage):
        node["children"].append(
            build_from_person(
                child,
                seen_marriages=seen_marriages,
                person_path=next_path,
                max_depth=max_depth - 1,
            )
        )
    return node


def root_people() -> QuerySet[Person]:
    child_ids = ParentChild.objects.values_list("child_id", flat=True)
    return Person.objects.exclude(id__in=child_ids).order_by("last_name", "first_name", "middle_name")


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
