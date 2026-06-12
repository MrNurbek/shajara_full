from __future__ import annotations

from django.db.models import Min, Q
from django.http import Http404
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Gender, Marriage, ParentChild, ParentType, Person, Photo
from .serializers import (
    MarriageWriteSerializer,
    ParentChildWriteSerializer,
    PersonDetailSerializer,
    PersonListSerializer,
    PersonWriteSerializer,
    PhotoSerializer,
    PhotoUploadSerializer,
)
from .services.family_ops import add_child, ensure_marriage
from .services.tree_builder import build_forest_all_roots


def safe_depth(value: str | None, default: int = 50) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, 100))


class FullTreePageView(TemplateView):
    template_name = "genealogy/tree.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["forest"] = build_forest_all_roots()
        context["people_count"] = Person.objects.count()
        context["marriage_count"] = Marriage.objects.count()
        context["link_count"] = ParentChild.objects.count()
        context["male_count"] = Person.objects.filter(gender=Gender.MALE).count()
        context["female_count"] = Person.objects.filter(gender=Gender.FEMALE).count()
        context["deceased_count"] = Person.objects.filter(death_date__isnull=False).count()
        context["photo_count"] = Photo.objects.count()
        context["oldest_birth_year"] = Person.objects.exclude(birth_date__isnull=True).aggregate(year=Min("birth_date"))["year"]
        context["can_edit_tree"] = bool(self.request.user.is_authenticated and self.request.user.is_staff)
        context["can_use_createusers"] = bool(self.request.user.is_authenticated and self.request.user.is_superuser)
        return context


class FullTreeDataAPIView(APIView):
    def get(self, request):
        max_depth = safe_depth(request.query_params.get("max_depth"))
        return Response(build_forest_all_roots(max_depth=max_depth))


class PersonDetailAPIView(APIView):
    def get(self, request, person_id):
        try:
            person = Person.objects.prefetch_related("addresses", "photos").get(id=person_id)
        except Person.DoesNotExist as exc:
            raise Http404("Person not found") from exc
        serializer = PersonDetailSerializer(person, context={"request": request})
        return Response(serializer.data)


class PersonSearchAPIView(APIView):
    def get(self, request):
        query = (request.query_params.get("q") or "").strip()
        queryset = Person.objects.all().order_by("last_name", "first_name")
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(middle_name__icontains=query)
                | Q(full_name_custom__icontains=query)
                | Q(occupation__icontains=query)
            )
        queryset = queryset[:50]
        serializer = PersonListSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)


class PersonCreateAPIView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = PersonWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        person = serializer.save()
        detail = PersonDetailSerializer(person, context={"request": request})
        return Response(detail.data, status=status.HTTP_201_CREATED)


class PersonUpdateAPIView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, person_id):
        try:
            person = Person.objects.get(id=person_id)
        except Person.DoesNotExist as exc:
            raise Http404("Person not found") from exc
        serializer = PersonWriteSerializer(person, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        person = serializer.save()
        detail = PersonDetailSerializer(person, context={"request": request})
        return Response(detail.data)


class MarriageCreateAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = MarriageWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            p1 = Person.objects.get(id=data["spouse1"])
            p2 = Person.objects.get(id=data["spouse2"])
        except Person.DoesNotExist as exc:
            raise Http404("Spouse not found") from exc
        marriage = ensure_marriage(
            [p1, p2],
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            location_text=data.get("location_text", ""),
            notes=data.get("notes", ""),
        )
        return Response({"id": str(marriage.id), "title": str(marriage)}, status=status.HTTP_201_CREATED)


class ParentChildCreateAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = ParentChildWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            child = Person.objects.get(id=data["child"])
        except Person.DoesNotExist as exc:
            raise Http404("Child not found") from exc

        relation_type = data.get("relation_type") or ParentType.BIOLOGICAL
        notes = data.get("notes", "")

        if data.get("marriage"):
            try:
                marriage = Marriage.objects.get(id=data["marriage"])
            except Marriage.DoesNotExist as exc:
                raise Http404("Marriage not found") from exc
            link = add_child(child, marriage, relation_type, notes)
        elif data.get("parent"):
            try:
                parent = Person.objects.get(id=data["parent"])
            except Person.DoesNotExist as exc:
                raise Http404("Parent not found") from exc
            link = add_child(child, [parent], relation_type, notes)
        else:
            try:
                p1 = Person.objects.get(id=data["parent1"])
                p2 = Person.objects.get(id=data["parent2"])
            except KeyError:
                return Response({"detail": "parent, marriage yoki parent1+parent2 yuborilishi kerak."}, status=status.HTTP_400_BAD_REQUEST)
            except Person.DoesNotExist as exc:
                raise Http404("Parent not found") from exc
            link = add_child(child, [p1, p2], relation_type, notes)

        return Response({"id": str(link.id), "title": str(link)}, status=status.HTTP_201_CREATED)


class PhotoUploadAPIView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = PhotoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        photo = serializer.save()
        return Response(PhotoSerializer(photo, context={"request": request}).data, status=status.HTTP_201_CREATED)
