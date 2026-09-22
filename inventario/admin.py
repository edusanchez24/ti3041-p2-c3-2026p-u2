from django.contrib import admin
from .models import Cliente, Producto, Venta

# Register your models here.

class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "precio", "stock")
    search_fields = ("nombre",)
    ordering = ("nombre", "stock")

admin.site.register(Producto, ProductoAdmin)
admin.site.register(Cliente)
admin.site.register(Venta)
