from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import QuerySet
from django.http import HttpRequest

from accounts.models.user import DocumentImage, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "full_name", "role", "is_approved", "is_onboarded")
    list_filter = ("role", "is_approved", "is_onboarded")
    search_fields = ("username", "email", "full_name")
    ordering = ("username",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "email",
                    "full_name",
                    "phone",
                    "telegram",
                    "role",
                    "is_approved",
                    "is_onboarded",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "full_name",
                    "phone",
                    "telegram",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(DocumentImage)
class DocumentImageAdmin(admin.ModelAdmin):
    list_display = ("user", "image", "created")
    list_filter = ("created",)
    search_fields = ("user__username", "user__full_name")
    ordering = ("-created",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[DocumentImage]:
        return super().get_queryset(request).select_related("user")
