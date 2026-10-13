from django.contrib import admin
from .models import Cliente, Producto, ProductoTalla, Venta, VentaDetalle

# Register your models here.

class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "precio", "stock", "activo")
    search_fields = ("nombre",)
    ordering = ("nombre", "stock")


class ProductoTallaInline(admin.TabularInline):
    model = ProductoTalla
    extra = 1


ProductoAdmin.inlines = (ProductoTallaInline,)

admin.site.register(Producto, ProductoAdmin)
admin.site.register(Cliente)


class VentaDetalleInline(admin.TabularInline):
    model = VentaDetalle
    extra = 1
    readonly_fields = ('subtotal',)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    inlines = (VentaDetalleInline,)
    list_display = ('id', 'fecha', 'cliente', 'rut_cliente', 'total')
    list_filter = ('fecha',)
    date_hierarchy = 'fecha'
    search_fields = ('rut_cliente', 'cliente__rut', 'cliente__nombre')
    ordering = ('-fecha',)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalcular_total()
