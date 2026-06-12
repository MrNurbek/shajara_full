from django.urls import path

from .views import (
    FullTreeDataAPIView,
    FullTreePageView,
    MarriageCreateAPIView,
    ParentChildCreateAPIView,
    PersonCreateAPIView,
    PersonDetailAPIView,
    PersonSearchAPIView,
    PersonUpdateAPIView,
    PhotoUploadAPIView,
)
from .createusers_views import (
    createusers_add_child,
    createusers_add_spouse,
    createusers_dashboard,
    createusers_login,
    createusers_logout,
    createusers_person_create,
    createusers_person_detail,
    createusers_person_edit,
)

app_name = "genealogy"

urlpatterns = [
    path("tree/", FullTreePageView.as_view(), name="tree"),

    # Custom superuser-only panel. Django admin emas.
    path("createusers/login/", createusers_login, name="createusers-login"),
    path("createusers/logout/", createusers_logout, name="createusers-logout"),
    path("createusers/", createusers_dashboard, name="createusers-dashboard"),
    path("createusers/person/create/", createusers_person_create, name="createusers-person-create"),
    path("createusers/person/<uuid:person_id>/", createusers_person_detail, name="createusers-person-detail"),
    path("createusers/person/<uuid:person_id>/edit/", createusers_person_edit, name="createusers-person-edit"),
    path("createusers/person/<uuid:person_id>/spouse/add/", createusers_add_spouse, name="createusers-add-spouse"),
    path("createusers/person/<uuid:person_id>/child/add/", createusers_add_child, name="createusers-add-child"),

    path("api/tree/", FullTreeDataAPIView.as_view(), name="tree-data"),
    path("api/people/", PersonSearchAPIView.as_view(), name="people-search"),
    path("api/people/create/", PersonCreateAPIView.as_view(), name="person-create"),
    path("api/people/<uuid:person_id>/", PersonDetailAPIView.as_view(), name="person-detail"),
    path("api/people/<uuid:person_id>/update/", PersonUpdateAPIView.as_view(), name="person-update"),
    path("api/marriages/create/", MarriageCreateAPIView.as_view(), name="marriage-create"),
    path("api/parent-child/create/", ParentChildCreateAPIView.as_view(), name="parent-child-create"),
    path("api/photos/create/", PhotoUploadAPIView.as_view(), name="photo-create"),
]
