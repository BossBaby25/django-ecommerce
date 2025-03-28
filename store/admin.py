from django.contrib import admin
from .models import Category, Product

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
