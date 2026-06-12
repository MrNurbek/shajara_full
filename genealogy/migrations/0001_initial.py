# Generated for the modernized Shajara project.
import django.db.models.deletion
import uuid
from django.db import migrations, models
from django.db.models import F, Q


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Address",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("country", models.CharField(blank=True, max_length=120, verbose_name="Davlat")),
                ("region", models.CharField(blank=True, max_length=120, verbose_name="Viloyat / hudud")),
                ("district", models.CharField(blank=True, max_length=120, verbose_name="Tuman")),
                ("city", models.CharField(blank=True, max_length=120, verbose_name="Shahar / qishloq")),
                ("street", models.CharField(blank=True, max_length=200, verbose_name="Ko‘cha")),
                ("house", models.CharField(blank=True, max_length=50, verbose_name="Uy")),
                ("postal_code", models.CharField(blank=True, max_length=20, verbose_name="Pochta indeksi")),
                ("description", models.CharField(blank=True, max_length=255, verbose_name="Izoh")),
            ],
            options={"verbose_name": "Manzil", "verbose_name_plural": "Manzillar", "ordering": ["country", "region", "district", "city", "street"]},
        ),
        migrations.CreateModel(
            name="Person",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("slug", models.SlugField(blank=True, db_index=True, max_length=180, unique=True, verbose_name="Slug")),
                ("first_name", models.CharField(max_length=120, verbose_name="Ism")),
                ("last_name", models.CharField(blank=True, max_length=120, verbose_name="Familiya")),
                ("middle_name", models.CharField(blank=True, max_length=120, verbose_name="Otasining ismi")),
                ("full_name_custom", models.CharField(blank=True, max_length=255, verbose_name="To‘liq ism")),
                ("gender", models.CharField(choices=[("M", "Erkak"), ("F", "Ayol"), ("U", "Noma’lum")], default="U", max_length=1, verbose_name="Jinsi")),
                ("birth_date", models.DateField(blank=True, null=True, verbose_name="Tug‘ilgan sana")),
                ("death_date", models.DateField(blank=True, null=True, verbose_name="Vafot etgan sana")),
                ("birth_place", models.CharField(blank=True, max_length=255, verbose_name="Tug‘ilgan joy")),
                ("death_place", models.CharField(blank=True, max_length=255, verbose_name="Vafot etgan joy")),
                ("occupation", models.CharField(blank=True, max_length=200, verbose_name="Kasbi")),
                ("biography", models.TextField(blank=True, verbose_name="Biografiya")),
                ("primary_photo", models.ImageField(blank=True, upload_to="people/primary/%Y/%m/", verbose_name="Asosiy rasm")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")),
                ("addresses", models.ManyToManyField(blank=True, related_name="residents", to="genealogy.address", verbose_name="Manzillar")),
            ],
            options={"verbose_name": "Shaxs", "verbose_name_plural": "Shaxslar", "ordering": ["last_name", "first_name", "middle_name"]},
        ),
        migrations.CreateModel(
            name="Marriage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("start_date", models.DateField(blank=True, null=True, verbose_name="Nikoh boshlangan sana")),
                ("end_date", models.DateField(blank=True, null=True, verbose_name="Nikoh tugagan sana")),
                ("location_text", models.CharField(blank=True, max_length=200, verbose_name="Joy")),
                ("notes", models.TextField(blank=True, verbose_name="Izoh")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")),
                ("spouse1", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="marriages_as_spouse1", to="genealogy.person", verbose_name="Turmush o‘rtoq 1")),
                ("spouse2", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="marriages_as_spouse2", to="genealogy.person", verbose_name="Turmush o‘rtoq 2")),
            ],
            options={"verbose_name": "Nikoh", "verbose_name_plural": "Nikohlar", "ordering": ["start_date", "id"]},
        ),
        migrations.CreateModel(
            name="Photo",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("image", models.ImageField(upload_to="people/photos/%Y/%m/", verbose_name="Rasm")),
                ("caption", models.CharField(blank=True, max_length=200, verbose_name="Sarlavha")),
                ("taken_at", models.DateField(blank=True, null=True, verbose_name="Olingan sana")),
                ("is_public", models.BooleanField(default=True, verbose_name="Ommaviy ko‘rinsin")),
                ("order_index", models.PositiveIntegerField(default=0, verbose_name="Tartib")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")),
                ("person", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="photos", to="genealogy.person", verbose_name="Shaxs")),
            ],
            options={"verbose_name": "Rasm", "verbose_name_plural": "Rasmlar", "ordering": ["order_index", "taken_at", "id"]},
        ),
        migrations.CreateModel(
            name="ParentChild",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("relation_type", models.CharField(choices=[("BIO", "Biologik"), ("ADP", "Asrab olingan"), ("STP", "O‘gay"), ("GRD", "Vasiy"), ("UNK", "Noma’lum")], default="BIO", max_length=3, verbose_name="Qarindoshlik turi")),
                ("notes", models.CharField(blank=True, max_length=255, verbose_name="Izoh")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")),
                ("child", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="parent_links", to="genealogy.person", verbose_name="Farzand")),
                ("marriage", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="child_links", to="genealogy.marriage", verbose_name="Nikoh orqali")),
                ("parent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="single_child_links", to="genealogy.person", verbose_name="Yolg‘iz ota/ona")),
            ],
            options={"verbose_name": "Ota-ona — farzand bog‘lanishi", "verbose_name_plural": "Ota-ona — farzand bog‘lanishlari"},
        ),
        migrations.AddIndex(model_name="person", index=models.Index(fields=["last_name", "first_name"], name="genealogy_p_last_na_5c5aca_idx")),
        migrations.AddIndex(model_name="person", index=models.Index(fields=["birth_date"], name="genealogy_p_birth_d_7e10d8_idx")),
        migrations.AddConstraint(model_name="marriage", constraint=models.CheckConstraint(condition=~Q(spouse1=F("spouse2")), name="marriage_spouses_must_differ")),
        migrations.AddConstraint(model_name="marriage", constraint=models.UniqueConstraint(fields=("spouse1", "spouse2"), name="uniq_canonical_marriage_pair")),
        migrations.AddIndex(model_name="parentchild", index=models.Index(fields=["child"], name="genealogy_p_child_i_78b4b2_idx")),
        migrations.AddIndex(model_name="parentchild", index=models.Index(fields=["marriage"], name="genealogy_p_marriag_e095a7_idx")),
        migrations.AddIndex(model_name="parentchild", index=models.Index(fields=["parent"], name="genealogy_p_parent__08cf55_idx")),
        migrations.AddConstraint(model_name="parentchild", constraint=models.CheckConstraint(condition=(Q(("marriage__isnull", False), ("parent__isnull", True)) | Q(("marriage__isnull", True), ("parent__isnull", False))), name="parent_child_exactly_one_parent_source")),
        migrations.AddConstraint(model_name="parentchild", constraint=models.UniqueConstraint(condition=Q(("marriage__isnull", False)), fields=("child", "marriage"), name="uniq_child_per_marriage")),
        migrations.AddConstraint(model_name="parentchild", constraint=models.UniqueConstraint(condition=Q(("parent__isnull", False)), fields=("child", "parent"), name="uniq_child_per_single_parent")),
    ]
