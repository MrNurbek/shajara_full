from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from genealogy.models import Address, Gender, ParentChild, Marriage, Person
from genealogy.services.family_ops import add_child, ensure_marriage


class Command(BaseCommand):
    help = "100 ta demo shajara ma’lumotini yaratadi: 10 ta oila, 5 avlodga yaqin bog‘lanishlar."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Faqat oldin seed_100 orqali yaratilgan Demo100 ma’lumotlarini o‘chirib, qayta yaratadi.",
        )
        parser.add_argument(
            "--clear-all",
            action="store_true",
            help="DIQQAT: barcha shajara ma’lumotlarini o‘chirib, 100 ta demo ma’lumot yaratadi.",
        )
        parser.add_argument(
            "--prefix",
            default="Demo100",
            help="Demo yozuvlarni ajratish uchun prefiks. Standart: Demo100",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        prefix = options["prefix"].strip() or "Demo100"

        if options["clear_all"]:
            ParentChild.objects.all().delete()
            Marriage.objects.all().delete()
            Person.objects.all().delete()
            Address.objects.all().delete()
            self.stdout.write(self.style.WARNING("Barcha mavjud shajara ma’lumotlari o‘chirildi."))
        elif options["clear"]:
            Person.objects.filter(full_name_custom__startswith=f"{prefix} ").delete()
            self.stdout.write(self.style.WARNING(f"{prefix} prefiksli demo ma’lumotlar o‘chirildi."))

        regions = [
            ("O‘zbekiston", "Surxondaryo", "Termiz", "Termiz shahri"),
            ("O‘zbekiston", "Toshkent", "Yunusobod", "Toshkent shahri"),
            ("O‘zbekiston", "Samarqand", "Samarqand", "Samarqand shahri"),
            ("O‘zbekiston", "Buxoro", "Buxoro", "Buxoro shahri"),
            ("O‘zbekiston", "Farg‘ona", "Marg‘ilon", "Marg‘ilon shahri"),
        ]
        addresses = []
        for country, region, district, city in regions:
            address, _ = Address.objects.get_or_create(
                country=country,
                region=region,
                district=district,
                city=city,
                defaults={"description": "Demo manzil"},
            )
            addresses.append(address)

        male_first = [
            "Abdulla", "Karim", "Hasan", "Husan", "Murod", "Sardor", "Javohir", "Aziz", "Bekzod", "Sherzod",
            "Jamshid", "Diyor", "Akmal", "Oybek", "Ulug‘bek", "Shahboz", "Nodir", "Temur", "Asad", "Rustam",
        ]
        female_first = [
            "Zaynab", "Malika", "Dilnoza", "Gulnoza", "Madina", "Sevara", "Nodira", "Dilorom", "Shahnoza", "Munisa",
            "Feruza", "Lola", "Mavluda", "Nigora", "Mohira", "Rayhona", "Umida", "Saida", "Aziza", "Gulsara",
        ]
        family_names = [
            "Karimov", "Abdullayev", "Tursunov", "Rahimov", "Norboyev", "Eshonqulov", "Saidov", "Qodirov", "Aliyev", "Umarov",
        ]
        occupations = [
            "O‘qituvchi", "Shifokor", "Muhandis", "Dasturchi", "Tadbirkor", "Fermer", "Huquqshunos", "Talaba", "Usta", "Ilmiy xodim",
        ]

        created_people: list[Person] = []

        def make_person(index: int, first_name: str, last_name: str, gender: str, birth_year: int, occupation: str, address: Address) -> Person:
            patronymic = "Azamat o‘g‘li" if gender == Gender.MALE else "Azamat qizi"
            custom_name = f"{prefix} {index:03d} — {last_name} {first_name}"
            person, _ = Person.objects.get_or_create(
                full_name_custom=custom_name,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "middle_name": patronymic,
                    "gender": gender,
                    "birth_date": date(birth_year, (index % 12) + 1, (index % 26) + 1),
                    "birth_place": f"{address.region}, {address.city}",
                    "occupation": occupation,
                    "biography": (
                        f"{custom_name} shajara loyihasini sinovdan o‘tkazish uchun yaratilgan demo shaxs. "
                        "Bu yozuv orqali genealogik daraxt, profil modal oynasi va qidiruv funksiyalari tekshiriladi."
                    ),
                },
            )
            person.addresses.add(address)
            if person not in created_people:
                created_people.append(person)
            return person

        counter = 1
        for family_index, base_last_name in enumerate(family_names, start=1):
            address = addresses[(family_index - 1) % len(addresses)]
            male_last_name = base_last_name
            female_last_name = base_last_name.replace("ov", "ova").replace("yev", "yeva")

            grandfather = make_person(
                counter, male_first[(family_index - 1) % len(male_first)], male_last_name,
                Gender.MALE, 1930 + family_index, occupations[0], address,
            )
            counter += 1
            grandmother = make_person(
                counter, female_first[(family_index - 1) % len(female_first)], female_last_name,
                Gender.FEMALE, 1934 + family_index, occupations[4], address,
            )
            counter += 1
            root_marriage = ensure_marriage([grandfather, grandmother], location_text=address.city)

            children = []
            for child_no in range(2):
                is_male = child_no == 0
                child_first = male_first[(family_index + child_no + 2) % len(male_first)] if is_male else female_first[(family_index + child_no + 2) % len(female_first)]
                child_last = male_last_name if is_male else female_last_name
                child = make_person(
                    counter, child_first, child_last,
                    Gender.MALE if is_male else Gender.FEMALE,
                    1960 + family_index + child_no,
                    occupations[(family_index + child_no) % len(occupations)],
                    address,
                )
                counter += 1
                add_child(child, root_marriage)
                children.append(child)

            for child_no, child in enumerate(children):
                child_is_male = child.gender == Gender.MALE
                spouse_gender = Gender.FEMALE if child_is_male else Gender.MALE
                spouse_first = female_first[(family_index + child_no + 6) % len(female_first)] if spouse_gender == Gender.FEMALE else male_first[(family_index + child_no + 6) % len(male_first)]
                spouse_last = female_last_name if spouse_gender == Gender.FEMALE else male_last_name
                spouse = make_person(
                    counter, spouse_first, spouse_last,
                    spouse_gender,
                    1962 + family_index + child_no,
                    occupations[(family_index + child_no + 3) % len(occupations)],
                    address,
                )
                counter += 1
                child_marriage = ensure_marriage([child, spouse], location_text=address.city)

                for grand_no in range(2):
                    grand_is_male = grand_no == 0
                    grand_first = male_first[(family_index + child_no + grand_no + 10) % len(male_first)] if grand_is_male else female_first[(family_index + child_no + grand_no + 10) % len(female_first)]
                    grand_last = male_last_name if grand_is_male else female_last_name
                    grandchild = make_person(
                        counter, grand_first, grand_last,
                        Gender.MALE if grand_is_male else Gender.FEMALE,
                        1990 + family_index + child_no + grand_no,
                        occupations[(family_index + child_no + grand_no + 6) % len(occupations)],
                        address,
                    )
                    counter += 1
                    add_child(grandchild, child_marriage)

        total_demo_people = Person.objects.filter(full_name_custom__startswith=f"{prefix} ").count()
        total_marriages = Marriage.objects.count()
        total_links = ParentChild.objects.count()

        self.stdout.write(self.style.SUCCESS(f"{total_demo_people} ta {prefix} demo shaxs bazaga qo‘shildi."))
        self.stdout.write(self.style.SUCCESS(f"Nikohlar soni: {total_marriages}; ota-ona/farzand bog‘lanishlari: {total_links}."))
