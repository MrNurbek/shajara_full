from django.core.management.base import BaseCommand
from django.db import transaction

from genealogy.models import Gender, Person
from genealogy.services.family_ops import add_child, ensure_marriage


class Command(BaseCommand):
    help = "Demo shajara ma’lumotlarini yaratadi."

    @transaction.atomic
    def handle(self, *args, **options):
        bob, _ = Person.objects.get_or_create(
            first_name="Abdulla", last_name="Karimov",
            defaults={"gender": Gender.MALE, "birth_place": "Termiz", "occupation": "Dehqon"},
        )
        buvi, _ = Person.objects.get_or_create(
            first_name="Zaynab", last_name="Karimova",
            defaults={"gender": Gender.FEMALE, "birth_place": "Termiz", "occupation": "Uy bekasi"},
        )
        ota, _ = Person.objects.get_or_create(
            first_name="Murod", last_name="Karimov",
            defaults={"gender": Gender.MALE, "birth_place": "Termiz", "occupation": "O‘qituvchi"},
        )
        ona, _ = Person.objects.get_or_create(
            first_name="Malika", last_name="Karimova",
            defaults={"gender": Gender.FEMALE, "birth_place": "Denov", "occupation": "Shifokor"},
        )
        farzand1, _ = Person.objects.get_or_create(
            first_name="Sardor", last_name="Karimov", defaults={"gender": Gender.MALE, "occupation": "Dasturchi"}
        )
        farzand2, _ = Person.objects.get_or_create(
            first_name="Dilnoza", last_name="Karimova", defaults={"gender": Gender.FEMALE, "occupation": "Talaba"}
        )

        ensure_marriage([bob, buvi], location_text="Termiz")
        add_child(ota, [bob, buvi])
        ensure_marriage([ota, ona], location_text="Termiz")
        add_child(farzand1, [ota, ona])
        add_child(farzand2, [ota, ona])
        self.stdout.write(self.style.SUCCESS("Demo shajara yaratildi."))
