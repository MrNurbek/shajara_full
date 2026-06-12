from __future__ import annotations

from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .createusers_forms import AddChildForm, AddSpouseForm, PersonForm
from .models import Gender, Marriage, ParentChild, Person
from .services.family_ops import add_child, ensure_marriage


CREATEUSERS_SESSION_KEY = "createusers_superuser_ok"


def _safe_next(request: HttpRequest, fallback: str) -> str:
    next_url = request.POST.get("next") or request.GET.get("next") or fallback
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return next_url
    return fallback


def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse("genealogy:createusers-login")
            return redirect(f"{login_url}?next={request.get_full_path()}")
        if not request.user.is_superuser:
            raise PermissionDenied("Bu paneldan faqat superuser foydalanishi mumkin.")
        return view_func(request, *args, **kwargs)

    return _wrapped


def create_person_from_cleaned(form, prefix: str) -> Person:
    kwargs = form.build_person_kwargs(prefix)
    return Person.objects.create(**kwargs)


@require_http_methods(["GET", "POST"])
def createusers_login(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect(_safe_next(request, reverse("genealogy:createusers-dashboard")))

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Login yoki parol noto‘g‘ri.")
        elif not user.is_superuser:
            messages.error(request, "Bu panelga faqat superuser kira oladi.")
        else:
            login(request, user)
            request.session[CREATEUSERS_SESSION_KEY] = True
            return redirect(_safe_next(request, reverse("genealogy:createusers-dashboard")))

    return render(request, "genealogy/createusers/login.html", {"next": request.GET.get("next", "")})


@superuser_required
def createusers_logout(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "CreateUsers panelidan chiqdingiz.")
    return redirect("genealogy:createusers-login")


@superuser_required
def createusers_dashboard(request: HttpRequest) -> HttpResponse:
    query = (request.GET.get("q") or "").strip()
    people = Person.objects.all().order_by("last_name", "first_name", "full_name_custom")
    if query:
        people = people.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(middle_name__icontains=query)
            | Q(full_name_custom__icontains=query)
            | Q(occupation__icontains=query)
        )

    people = people.annotate(parent_link_count=Count("parent_links", distinct=True))
    paginator = Paginator(people, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "q": query,
        "page_obj": page_obj,
        "people_count": Person.objects.count(),
        "marriage_count": Marriage.objects.count(),
        "parent_child_count": ParentChild.objects.count(),
        "male_count": Person.objects.filter(gender=Gender.MALE).count(),
        "female_count": Person.objects.filter(gender=Gender.FEMALE).count(),
    }
    return render(request, "genealogy/createusers/dashboard.html", context)


@superuser_required
@require_http_methods(["GET", "POST"])
def createusers_person_create(request: HttpRequest) -> HttpResponse:
    form = PersonForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        person = form.save()
        messages.success(request, f"{person.display_name} qo‘shildi.")
        return redirect("genealogy:createusers-person-detail", person_id=person.id)
    return render(request, "genealogy/createusers/person_form.html", {"form": form, "title": "Yangi shaxs qo‘shish"})


@superuser_required
@require_http_methods(["GET", "POST"])
def createusers_person_edit(request: HttpRequest, person_id) -> HttpResponse:
    person = get_object_or_404(Person, id=person_id)
    form = PersonForm(request.POST or None, request.FILES or None, instance=person)
    if request.method == "POST" and form.is_valid():
        person = form.save()
        messages.success(request, f"{person.display_name} yangilandi.")
        return redirect("genealogy:createusers-person-detail", person_id=person.id)
    return render(request, "genealogy/createusers/person_form.html", {"form": form, "person": person, "title": "Shaxsni tahrirlash"})


def person_relations(person: Person) -> dict:
    marriages = Marriage.objects.filter(Q(spouse1=person) | Q(spouse2=person)).select_related("spouse1", "spouse2")
    spouses = [m.other_partner(person) for m in marriages if m.other_partner(person)]

    parent_links = ParentChild.objects.filter(child=person).select_related("parent", "marriage", "marriage__spouse1", "marriage__spouse2")
    parents = []
    for link in parent_links:
        if link.parent_id:
            parents.append(link.parent)
        elif link.marriage_id:
            parents.extend([link.marriage.spouse1, link.marriage.spouse2])

    children = []
    seen = set()
    for link in ParentChild.objects.filter(parent=person).select_related("child"):
        if link.child_id not in seen:
            seen.add(link.child_id)
            children.append(link.child)
    for marriage in marriages:
        for link in marriage.child_links.select_related("child"):
            if link.child_id not in seen:
                seen.add(link.child_id)
                children.append(link.child)

    return {"marriages": marriages, "spouses": spouses, "parents": parents, "children": children}


@superuser_required
def createusers_person_detail(request: HttpRequest, person_id) -> HttpResponse:
    person = get_object_or_404(Person, id=person_id)
    context = {"person": person, **person_relations(person)}
    return render(request, "genealogy/createusers/person_detail.html", context)


@superuser_required
@require_http_methods(["GET", "POST"])
def createusers_add_spouse(request: HttpRequest, person_id) -> HttpResponse:
    person = get_object_or_404(Person, id=person_id)
    form = AddSpouseForm(request.POST or None, person=person)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                if form.cleaned_data["mode"] == "existing":
                    spouse = form.cleaned_data["existing_spouse"]
                else:
                    spouse = create_person_from_cleaned(form, "spouse")
                marriage = ensure_marriage(
                    [person, spouse],
                    start_date=form.cleaned_data.get("start_date"),
                    end_date=form.cleaned_data.get("end_date"),
                    location_text=form.cleaned_data.get("location_text") or "",
                    notes=form.cleaned_data.get("notes") or "",
                )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, f"{person.display_name} va {spouse.display_name} nikohi bog‘landi.")
            return redirect("genealogy:createusers-person-detail", person_id=person.id)
    return render(request, "genealogy/createusers/add_spouse.html", {"form": form, "person": person})


@superuser_required
@require_http_methods(["GET", "POST"])
def createusers_add_child(request: HttpRequest, person_id) -> HttpResponse:
    person = get_object_or_404(Person, id=person_id)
    form = AddChildForm(request.POST or None, person=person)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                if form.cleaned_data["mode"] == "existing":
                    child = form.cleaned_data["existing_child"]
                else:
                    child = create_person_from_cleaned(form, "child")
                other_parent = form.cleaned_data.get("other_parent")
                relation_type = form.cleaned_data.get("relation_type") or "BIO"
                notes = form.cleaned_data.get("notes") or ""
                if other_parent:
                    marriage = ensure_marriage([person, other_parent])
                    add_child(child, marriage, relation_type, notes)
                else:
                    add_child(child, [person], relation_type, notes)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, f"{child.display_name} farzand sifatida bog‘landi.")
            return redirect("genealogy:createusers-person-detail", person_id=person.id)
    return render(request, "genealogy/createusers/add_child.html", {"form": form, "person": person})
