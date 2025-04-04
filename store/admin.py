from django.contrib import admin
from .models import Category, Product , Order
from .models import Feedback

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)

    def get_queryset(self, request):
        """
        Restrict product management to admins only.
        """
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            return queryset.none()
        return queryset

    def has_add_permission(self, request):
        """
        Only superusers (admins) can add products.
        """
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """
        Only superusers (admins) can edit products.
        """
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """
        Only superusers (admins) can delete products.
        """
        return request.user.is_superuser

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_price", "display_products_info", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username",)
    ordering = ("-created_at",)
    list_editable = ("status",)

    def display_products_info(self, obj):
        return obj.products_info
    display_products_info.short_description = "Ordered Items"



@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "submitted_at")
    search_fields = ("user__username", "message")
    readonly_fields = ("user", "message", "submitted_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
