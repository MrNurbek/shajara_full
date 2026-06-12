from django import forms
from django.contrib import admin, messages
from django.db import transaction
from django.template.response import TemplateResponse

from .models import Address, Marriage, ParentChild, ParentType, Person, Photo
from .services.family_ops import add_child, ensure_marriage


class DateInput(forms.DateInput):
    input_type = "date"


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 0
    fields = ("image", "caption", "taken_at", "is_public", "order_index")


class ParentChildInline(admin.TabularInline):
    model = ParentChild
    fk_name = "child"
    extra = 0
    fields = ("marriage", "parent", "relation_type", "notes")
    autocomplete_fields = ("marriage", "parent")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("display_name", "gender", "birth_date", "death_date", "occupation", "updated_at")
    list_filter = ("gender", "birth_date", "death_date")
    search_fields = ("first_name", "last_name", "middle_name", "full_name_custom", "occupation", "biography", "slug")
    readonly_fields = ("id", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("last_name", "first_name", "middle_name")}
    filter_horizontal = ("addresses",)
    inlines = (PhotoInline, ParentChildInline)
    fieldsets = (
        ("Asosiy ma’lumotlar", {"fields": ("id", "slug", "first_name", "last_name", "middle_name", "full_name_custom", "gender")} ),
        ("Hayotiy ma’lumotlar", {"fields": ("birth_date", "birth_place", "death_date", "death_place", "occupation", "biography")} ),
        ("Media va manzil", {"fields": ("primary_photo", "addresses")} ),
        ("Tizim", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    class CreateMarriageForm(forms.Form):
        start_date = forms.DateField(required=False, label="Boshlanish sanasi", widget=DateInput)
        end_date = forms.DateField(required=False, label="Tugash sanasi", widget=DateInput)
        location_text = forms.CharField(required=False, max_length=200, label="Joy")
        notes = forms.CharField(required=False, widget=forms.Textarea, label="Izoh")

    class AddChildTwoParentsForm(forms.Form):
        parent1 = forms.ModelChoiceField(queryset=Person.objects.all(), label="Ota/ona 1")
        parent2 = forms.ModelChoiceField(queryset=Person.objects.all(), label="Ota/ona 2")
        relation_type = forms.ChoiceField(choices=ParentType.choices, initial=ParentType.BIOLOGICAL, label="Qarindoshlik turi")

    class AddChildSingleParentForm(forms.Form):
        parent = forms.ModelChoiceField(queryset=Person.objects.all(), label="Yolg‘iz ota/ona")
        relation_type = forms.ChoiceField(choices=ParentType.choices, initial=ParentType.BIOLOGICAL, label="Qarindoshlik turi")

    @admin.action(description="Belgilangan 2 shaxs uchun nikoh yaratish yoki mavjudini yangilash")
    def create_or_attach_marriage(self, request, queryset):
        if queryset.count() != 2:
            self.message_user(request, "Aynan 2 ta shaxs belgilang.", level=messages.ERROR)
            return None
        form = self.CreateMarriageForm(request.POST or None)
        if "apply" in request.POST and form.is_valid():
            try:
                with transaction.atomic():
                    marriage = ensure_marriage(list(queryset), **form.cleaned_data)
                self.message_user(request, f"Nikoh saqlandi: {marriage}", level=messages.SUCCESS)
            except Exception as exc:
                self.message_user(request, f"Xato: {exc}", level=messages.ERROR)
            return None
        context = {
            **self.admin_site.each_context(request),
            "title": "Nikoh yaratish yoki ulash",
            "form": form,
            "objects": queryset,
            "action": "create_or_attach_marriage",
            "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
        }
        return TemplateResponse(request, "admin/actions/simple_form_action.html", context)

    @admin.action(description="Belgilangan 1 bolani ikki ota-onaga bog‘lash")
    def add_child_to_two_parents(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Aynan 1 ta bola belgilang.", level=messages.ERROR)
            return None
        child = queryset.first()
        form = self.AddChildTwoParentsForm(request.POST or None)
        if "apply" in request.POST and form.is_valid():
            try:
                add_child(child, [form.cleaned_data["parent1"], form.cleaned_data["parent2"]], form.cleaned_data["relation_type"])
                self.message_user(request, f"Bog‘landi: {child}", level=messages.SUCCESS)
            except Exception as exc:
                self.message_user(request, f"Xato: {exc}", level=messages.ERROR)
            return None
        context = {
            **self.admin_site.each_context(request),
            "title": "Bolani ikki ota-onaga bog‘lash",
            "form": form,
            "objects": queryset,
            "action": "add_child_to_two_parents",
            "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
        }
        return TemplateResponse(request, "admin/actions/simple_form_action.html", context)

    @admin.action(description="Belgilangan 1 bolani yolg‘iz ota/onaga bog‘lash")
    def add_child_to_single_parent(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Aynan 1 ta bola belgilang.", level=messages.ERROR)
            return None
        child = queryset.first()
        form = self.AddChildSingleParentForm(request.POST or None)
        if "apply" in request.POST and form.is_valid():
            try:
                add_child(child, [form.cleaned_data["parent"]], form.cleaned_data["relation_type"])
                self.message_user(request, f"Bog‘landi: {child}", level=messages.SUCCESS)
            except Exception as exc:
                self.message_user(request, f"Xato: {exc}", level=messages.ERROR)
            return None
        context = {
            **self.admin_site.each_context(request),
            "title": "Bolani yolg‘iz ota/onaga bog‘lash",
            "form": form,
            "objects": queryset,
            "action": "add_child_to_single_parent",
            "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
        }
        return TemplateResponse(request, "admin/actions/simple_form_action.html", context)

    actions = ("create_or_attach_marriage", "add_child_to_two_parents", "add_child_to_single_parent")


@admin.register(Marriage)
class MarriageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "start_date", "end_date", "location_text", "created_at")
    list_filter = ("start_date", "end_date")
    search_fields = (
        "location_text", "notes",
        "spouse1__first_name", "spouse1__last_name", "spouse1__full_name_custom",
        "spouse2__first_name", "spouse2__last_name", "spouse2__full_name_custom",
    )
    autocomplete_fields = ("spouse1", "spouse2")
    readonly_fields = ("id", "created_at")


@admin.register(ParentChild)
class ParentChildAdmin(admin.ModelAdmin):
    list_display = ("child", "marriage", "parent", "relation_type", "created_at")
    list_filter = ("relation_type",)
    search_fields = (
        "child__first_name", "child__last_name", "child__full_name_custom",
        "parent__first_name", "parent__last_name", "parent__full_name_custom", "notes",
    )
    autocomplete_fields = ("child", "marriage", "parent")
    readonly_fields = ("id", "created_at")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("country", "region", "district", "city", "street", "house", "postal_code")
    search_fields = ("country", "region", "district", "city", "street", "house", "postal_code", "description")


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("person", "caption", "taken_at", "is_public", "order_index", "created_at")
    list_filter = ("is_public", "taken_at")
    search_fields = ("caption", "person__first_name", "person__last_name", "person__full_name_custom")
    autocomplete_fields = ("person",)
    readonly_fields = ("id", "created_at")
