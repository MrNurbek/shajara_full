from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Gender, Marriage, ParentChild, Person
from .services.family_ops import add_child, ensure_marriage
from .services.tree_builder import build_forest_all_roots


class GenealogyModelTests(TestCase):
    def setUp(self):
        self.father = Person.objects.create(first_name="Ali", last_name="Valiyev", gender=Gender.MALE)
        self.mother = Person.objects.create(first_name="Malika", last_name="Valiyeva", gender=Gender.FEMALE)
        self.child = Person.objects.create(first_name="Aziz", last_name="Valiyev", gender=Gender.MALE)

    def test_marriage_is_canonical_and_unique(self):
        first = ensure_marriage([self.father, self.mother])
        second = ensure_marriage([self.mother, self.father])
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Marriage.objects.count(), 1)

    def test_child_link_created_once(self):
        add_child(self.child, [self.father, self.mother])
        add_child(self.child, [self.mother, self.father])
        self.assertEqual(ParentChild.objects.count(), 1)

    def test_person_cannot_be_own_parent(self):
        with self.assertRaises(ValidationError):
            add_child(self.child, [self.child])

    def test_tree_builder_returns_root(self):
        add_child(self.child, [self.father, self.mother])
        tree = build_forest_all_roots()
        self.assertEqual(tree["type"], "root")
        self.assertTrue(tree["children"])


class GenealogyApiTests(TestCase):
    def test_tree_api_accepts_invalid_depth_safely(self):
        response = self.client.get(reverse("genealogy:tree-data"), {"max_depth": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["type"], "root")
