from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models.user import DocumentImage, User


class CustomUserAdmin(UserAdmin):
    # Define the fields to be displayed in the list view
    list_display = (
        "phone",
        "full_name",
        "telegram",
        "role",
        "address",
        "company",
        "email",
        "is_approved",
        "is_onboarded",
        "is_superuser",
        "date_joined",
    )
    list_editable = ("is_approved", "is_onboarded")

    fieldsets = (
        ("User", {"fields": ("phone", "password")}),
        ("Personal info", {"fields": ("full_name", "telegram", "tg_user_id", "email", "address", "company")}),
        (
            "Permissions",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_approved",
                    "is_onboarded",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    # Define the fields to be used when adding a new user
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone",
                    "full_name",
                    "telegram",
                    "password1",
                    "password2",
                    "role",
                    "address",
                    "company",
                    "email",
                    "is_approved",
                    "is_onboarded",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )

    # Define the fields to be used for searching
    search_fields = ("phone", "full_name", "telegram")

    # Define the fields to be used for filtering
    list_filter = ("role", "is_approved", "is_staff")

    # Define the ordering of the list view
    ordering = ("full_name", "date_joined")


admin.site.register(User, CustomUserAdmin)


class DocumentImageAdmin(admin.ModelAdmin):
    list_display = ("user", "image", "created")

    search_fields = ("user__phone", "user__full_name")

    list_filter = ("created", "user__role")

    ordering = ("-created",)


admin.site.register(DocumentImage, DocumentImageAdmin)
