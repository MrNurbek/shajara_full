from __future__ import annotations

from django import forms

from .models import Gender, Person, ParentType


class PersonChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: Person) -> str:
        years = []
        if obj.birth_year:
            years.append(str(obj.birth_year))
        if obj.death_year:
            years.append(str(obj.death_year))
        suffix = f" ({'–'.join(years)})" if years else ""
        return f"{obj.display_name}{suffix}"


COMMON_INPUT = {"class": "cu-input"}
COMMON_SELECT = {"class": "cu-input cu-select"}
COMMON_TEXTAREA = {"class": "cu-input", "rows": 4}


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = (
            "full_name_custom",
            "first_name",
            "last_name",
            "middle_name",
            "gender",
            "birth_date",
            "death_date",
            "birth_place",
            "death_place",
            "occupation",
            "biography",
            "primary_photo",
        )
        widgets = {
            "full_name_custom": forms.TextInput(attrs={**COMMON_INPUT, "placeholder": "Masalan: Omonkeldi"}),
            "first_name": forms.TextInput(attrs={**COMMON_INPUT, "placeholder": "Ism"}),
            "last_name": forms.TextInput(attrs={**COMMON_INPUT, "placeholder": "Familiya (bo‘lsa)"}),
            "middle_name": forms.TextInput(attrs={**COMMON_INPUT, "placeholder": "Otasining ismi (bo‘lsa)"}),
            "gender": forms.Select(attrs=COMMON_SELECT),
            "birth_date": forms.DateInput(attrs={**COMMON_INPUT, "type": "date"}),
            "death_date": forms.DateInput(attrs={**COMMON_INPUT, "type": "date"}),
            "birth_place": forms.TextInput(attrs=COMMON_INPUT),
            "death_place": forms.TextInput(attrs=COMMON_INPUT),
            "occupation": forms.TextInput(attrs=COMMON_INPUT),
            "biography": forms.Textarea(attrs=COMMON_TEXTAREA),
            "primary_photo": forms.ClearableFileInput(attrs={"class": "cu-file"}),
        }
        labels = {
            "full_name_custom": "To‘liq ism",
            "first_name": "Ism",
            "last_name": "Familiya",
            "middle_name": "Otasining ismi",
            "gender": "Jinsi",
            "birth_date": "Tug‘ilgan sana",
            "death_date": "Vafot sanasi",
            "birth_place": "Tug‘ilgan joy",
            "death_place": "Vafot joyi",
            "occupation": "Kasbi",
            "biography": "Izoh / biografiya",
            "primary_photo": "Rasm",
        }

    def clean(self):
        cleaned = super().clean()
        first_name = (cleaned.get("first_name") or "").strip()
        full_name = (cleaned.get("full_name_custom") or "").strip()
        if not first_name and full_name:
            cleaned["first_name"] = full_name.split()[0]
        if not cleaned.get("first_name"):
            raise forms.ValidationError("Kamida ism yoki to‘liq ism kiritilishi kerak.")
        return cleaned


class QuickPersonFieldsMixin:
    def add_quick_person_fields(self, prefix: str, title: str):
        self.fields[f"{prefix}_full_name_custom"] = forms.CharField(
            label=f"{title} — to‘liq ism",
            required=False,
            widget=forms.TextInput(attrs={**COMMON_INPUT, "placeholder": "To‘liq ism"}),
        )
        self.fields[f"{prefix}_first_name"] = forms.CharField(
            label=f"{title} — ism",
            required=False,
            widget=forms.TextInput(attrs={**COMMON_INPUT, "placeholder": "Ism"}),
        )
        self.fields[f"{prefix}_last_name"] = forms.CharField(
            label=f"{title} — familiya",
            required=False,
            widget=forms.TextInput(attrs={**COMMON_INPUT, "placeholder": "Familiya"}),
        )
        self.fields[f"{prefix}_middle_name"] = forms.CharField(
            label=f"{title} — otasining ismi",
            required=False,
            widget=forms.TextInput(attrs={**COMMON_INPUT, "placeholder": "Otasining ismi"}),
        )
        self.fields[f"{prefix}_gender"] = forms.ChoiceField(
            label=f"{title} — jinsi",
            required=False,
            choices=Gender.choices,
            initial=Gender.UNKNOWN,
            widget=forms.Select(attrs=COMMON_SELECT),
        )
        self.fields[f"{prefix}_birth_date"] = forms.DateField(
            label=f"{title} — tug‘ilgan sana",
            required=False,
            widget=forms.DateInput(attrs={**COMMON_INPUT, "type": "date"}),
        )
        self.fields[f"{prefix}_death_date"] = forms.DateField(
            label=f"{title} — vafot sanasi",
            required=False,
            widget=forms.DateInput(attrs={**COMMON_INPUT, "type": "date"}),
        )
        self.fields[f"{prefix}_notes"] = forms.CharField(
            label=f"{title} — izoh",
            required=False,
            widget=forms.Textarea(attrs={**COMMON_TEXTAREA, "rows": 3}),
        )

    def build_person_kwargs(self, prefix: str) -> dict:
        full_name = (self.cleaned_data.get(f"{prefix}_full_name_custom") or "").strip()
        first_name = (self.cleaned_data.get(f"{prefix}_first_name") or "").strip()
        if not first_name and full_name:
            first_name = full_name.split()[0]
        return {
            "full_name_custom": full_name,
            "first_name": first_name,
            "last_name": (self.cleaned_data.get(f"{prefix}_last_name") or "").strip(),
            "middle_name": (self.cleaned_data.get(f"{prefix}_middle_name") or "").strip(),
            "gender": self.cleaned_data.get(f"{prefix}_gender") or Gender.UNKNOWN,
            "birth_date": self.cleaned_data.get(f"{prefix}_birth_date"),
            "death_date": self.cleaned_data.get(f"{prefix}_death_date"),
            "biography": (self.cleaned_data.get(f"{prefix}_notes") or "").strip(),
        }

    def new_person_has_name(self, prefix: str) -> bool:
        return bool(
            (self.cleaned_data.get(f"{prefix}_full_name_custom") or "").strip()
            or (self.cleaned_data.get(f"{prefix}_first_name") or "").strip()
        )


class AddSpouseForm(QuickPersonFieldsMixin, forms.Form):
    mode = forms.ChoiceField(
        label="Qo‘shish turi",
        choices=(("existing", "Mavjud shaxsni tanlash"), ("new", "Yangi shaxs yaratish")),
        widget=forms.RadioSelect(attrs={"class": "cu-radio"}),
        initial="new",
    )
    existing_spouse = PersonChoiceField(
        label="Mavjud shaxs",
        queryset=Person.objects.none(),
        required=False,
        widget=forms.Select(attrs=COMMON_SELECT),
    )
    start_date = forms.DateField(label="Nikoh boshlangan sana", required=False, widget=forms.DateInput(attrs={**COMMON_INPUT, "type": "date"}))
    end_date = forms.DateField(label="Nikoh tugagan sana", required=False, widget=forms.DateInput(attrs={**COMMON_INPUT, "type": "date"}))
    location_text = forms.CharField(label="Nikoh joyi", required=False, widget=forms.TextInput(attrs=COMMON_INPUT))
    notes = forms.CharField(label="Nikoh izohi", required=False, widget=forms.Textarea(attrs={**COMMON_TEXTAREA, "rows": 3}))

    def __init__(self, *args, person: Person, **kwargs):
        super().__init__(*args, **kwargs)
        self.person = person
        self.fields["existing_spouse"].queryset = Person.objects.exclude(id=person.id).order_by("last_name", "first_name", "full_name_custom")
        self.add_quick_person_fields("spouse", "Yangi turmush o‘rtoq")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("mode") == "existing" and not cleaned.get("existing_spouse"):
            raise forms.ValidationError("Mavjud shaxs tanlanishi kerak.")
        if cleaned.get("mode") == "new" and not self.new_person_has_name("spouse"):
            raise forms.ValidationError("Yangi turmush o‘rtoq uchun ism yoki to‘liq ism kiriting.")
        return cleaned


class AddChildForm(QuickPersonFieldsMixin, forms.Form):
    mode = forms.ChoiceField(
        label="Farzand turi",
        choices=(("existing", "Mavjud shaxsni farzand qilish"), ("new", "Yangi farzand yaratish")),
        widget=forms.RadioSelect(attrs={"class": "cu-radio"}),
        initial="new",
    )
    existing_child = PersonChoiceField(
        label="Mavjud farzand",
        queryset=Person.objects.none(),
        required=False,
        widget=forms.Select(attrs=COMMON_SELECT),
    )
    other_parent = PersonChoiceField(
        label="Ikkinchi ota/ona yoki turmush o‘rtoq (ixtiyoriy)",
        queryset=Person.objects.none(),
        required=False,
        widget=forms.Select(attrs=COMMON_SELECT),
    )
    relation_type = forms.ChoiceField(
        label="Qarindoshlik turi",
        choices=ParentType.choices,
        initial=ParentType.BIOLOGICAL,
        required=False,
        widget=forms.Select(attrs=COMMON_SELECT),
    )
    notes = forms.CharField(label="Bog‘lanish izohi", required=False, widget=forms.Textarea(attrs={**COMMON_TEXTAREA, "rows": 3}))

    def __init__(self, *args, person: Person, **kwargs):
        super().__init__(*args, **kwargs)
        self.person = person
        base_qs = Person.objects.exclude(id=person.id).order_by("last_name", "first_name", "full_name_custom")
        self.fields["existing_child"].queryset = base_qs
        self.fields["other_parent"].queryset = base_qs
        self.add_quick_person_fields("child", "Yangi farzand")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("mode") == "existing" and not cleaned.get("existing_child"):
            raise forms.ValidationError("Mavjud farzand tanlanishi kerak.")
        if cleaned.get("mode") == "new" and not self.new_person_has_name("child"):
            raise forms.ValidationError("Yangi farzand uchun ism yoki to‘liq ism kiriting.")
        if cleaned.get("existing_child") and cleaned.get("existing_child") == cleaned.get("other_parent"):
            raise forms.ValidationError("Farzand va ikkinchi ota/ona bir xil shaxs bo‘la olmaydi.")
        return cleaned
