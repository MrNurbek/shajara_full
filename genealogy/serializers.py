from __future__ import annotations

from datetime import date
from django.db.models import Q
from rest_framework import serializers

from .models import Address, Marriage, ParentChild, Person, Photo


class AbsoluteImageMixin:
    def absolute_url(self, value) -> str:
        if not value:
            return ""
        request = self.context.get("request") if hasattr(self, "context") else None
        url = value.url
        return request.build_absolute_uri(url) if request else url


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ("id", "country", "region", "district", "city", "street", "house", "postal_code", "description")


class PhotoSerializer(AbsoluteImageMixin, serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = ("id", "image_url", "caption", "taken_at", "is_public", "order_index")

    def get_image_url(self, obj: Photo) -> str:
        return self.absolute_url(obj.image)


class MiniPersonSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    gender = serializers.CharField()
    birth_year = serializers.IntegerField(allow_null=True)
    death_year = serializers.IntegerField(allow_null=True)
    is_deceased = serializers.BooleanField()


def mini_from_person(person: Person) -> dict:
    return {
        "id": str(person.id),
        "name": person.display_name,
        "gender": person.gender,
        "birth_year": person.birth_year,
        "death_year": person.death_year,
        "is_deceased": person.is_deceased,
    }


class PersonDetailSerializer(AbsoluteImageMixin, serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    birth_year = serializers.IntegerField(read_only=True, allow_null=True)
    death_year = serializers.IntegerField(read_only=True, allow_null=True)
    is_deceased = serializers.BooleanField(read_only=True)
    primary_photo_url = serializers.SerializerMethodField()
    addresses = AddressSerializer(many=True, read_only=True)
    photos = serializers.SerializerMethodField()
    marriages = serializers.SerializerMethodField()
    spouses = serializers.SerializerMethodField()
    parents = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = (
            "id", "slug", "first_name", "last_name", "middle_name", "full_name_custom", "full_name", "gender",
            "birth_date", "death_date", "birth_year", "death_year", "age", "is_deceased",
            "birth_place", "death_place", "occupation", "biography",
            "primary_photo_url", "photos", "addresses",
            "marriages", "spouses", "parents", "children",
        )

    def get_full_name(self, obj: Person) -> str:
        return obj.display_name

    def get_age(self, obj: Person) -> int | None:
        if not obj.birth_date:
            return None
        endpoint = obj.death_date or date.today()
        return endpoint.year - obj.birth_date.year - ((endpoint.month, endpoint.day) < (obj.birth_date.month, obj.birth_date.day))

    def get_primary_photo_url(self, obj: Person) -> str:
        return self.absolute_url(obj.primary_photo)

    def get_photos(self, obj: Person) -> list[dict]:
        qs = obj.photos.filter(is_public=True).order_by("order_index", "taken_at", "id")
        return PhotoSerializer(qs, many=True, context=self.context).data

    def _marriages_qs(self, obj: Person):
        return Marriage.objects.filter(Q(spouse1=obj) | Q(spouse2=obj)).select_related("spouse1", "spouse2")

    def get_marriages(self, obj: Person) -> list[dict]:
        output: list[dict] = []
        for marriage in self._marriages_qs(obj):
            output.append(
                {
                    "id": str(marriage.id),
                    "start_date": marriage.start_date,
                    "end_date": marriage.end_date,
                    "location_text": marriage.location_text,
                    "notes": marriage.notes,
                    "spouses": [mini_from_person(marriage.spouse1), mini_from_person(marriage.spouse2)],
                }
            )
        return output

    def get_spouses(self, obj: Person) -> list[dict]:
        spouses: list[dict] = []
        seen: set[str] = set()
        for marriage in self._marriages_qs(obj):
            other = marriage.other_partner(obj)
            if other and str(other.id) not in seen:
                seen.add(str(other.id))
                spouses.append(mini_from_person(other))
        return spouses

    def get_parents(self, obj: Person) -> list[dict]:
        links = ParentChild.objects.filter(child=obj).select_related("marriage", "parent", "marriage__spouse1", "marriage__spouse2")
        output: list[dict] = []
        involved: set[str] = set()

        for link in links:
            if not link.marriage_id:
                continue
            parents = sorted(
                [link.marriage.spouse1, link.marriage.spouse2],
                key=lambda p: (0 if p.gender == "M" else 1 if p.gender == "F" else 2, p.display_name.lower()),
            )
            output.append({"parent": mini_from_person(parents[0]), "other_parent": mini_from_person(parents[1]), "via": "marriage"})
            involved.update({str(parents[0].id), str(parents[1].id)})

        for link in links:
            if link.parent_id and str(link.parent_id) not in involved:
                output.append({"parent": mini_from_person(link.parent), "other_parent": None, "via": "single"})
        output.sort(key=lambda item: item["parent"]["name"].lower())
        return output

    def get_children(self, obj: Person) -> list[dict]:
        output: list[dict] = []
        seen: set[tuple[str, str, str | None]] = set()

        for marriage in self._marriages_qs(obj):
            other = marriage.other_partner(obj)
            for link in marriage.child_links.select_related("child"):
                item = {
                    "child": mini_from_person(link.child),
                    "via": "marriage",
                    "other_parent": mini_from_person(other) if other else None,
                }
                key = (item["child"]["id"], item["via"], item["other_parent"]["id"] if item["other_parent"] else None)
                if key not in seen:
                    seen.add(key)
                    output.append(item)

        for link in ParentChild.objects.filter(parent=obj).select_related("child"):
            item = {"child": mini_from_person(link.child), "via": "single", "other_parent": None}
            key = (item["child"]["id"], item["via"], None)
            if key not in seen:
                seen.add(key)
                output.append(item)
        output.sort(key=lambda item: item["child"]["name"].lower())
        return output


class PersonListSerializer(AbsoluteImageMixin, serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    primary_photo_url = serializers.SerializerMethodField()
    birth_year = serializers.IntegerField(read_only=True, allow_null=True)
    death_year = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Person
        fields = ("id", "slug", "full_name", "gender", "birth_year", "death_year", "primary_photo_url")

    def get_full_name(self, obj: Person) -> str:
        return obj.display_name

    def get_primary_photo_url(self, obj: Person) -> str:
        return self.absolute_url(obj.primary_photo)


class PersonWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = (
            "first_name", "last_name", "middle_name", "full_name_custom", "gender",
            "birth_date", "death_date", "birth_place", "death_place", "occupation", "biography",
            "primary_photo",
        )
        extra_kwargs = {
            "first_name": {"required": True},
            "primary_photo": {"required": False},
        }


class MarriageWriteSerializer(serializers.Serializer):
    spouse1 = serializers.UUIDField()
    spouse2 = serializers.UUIDField()
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    location_text = serializers.CharField(required=False, allow_blank=True, max_length=200)
    notes = serializers.CharField(required=False, allow_blank=True)


class ParentChildWriteSerializer(serializers.Serializer):
    child = serializers.UUIDField()
    parent = serializers.UUIDField(required=False)
    parent1 = serializers.UUIDField(required=False)
    parent2 = serializers.UUIDField(required=False)
    marriage = serializers.UUIDField(required=False)
    relation_type = serializers.CharField(required=False, allow_blank=True, max_length=3)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=255)


class PhotoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ("person", "image", "caption", "taken_at", "is_public", "order_index")
