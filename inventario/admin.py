from django.contrib import admin
from django.db.models import Sum
from django.utils.dateparse import parse_date
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
    # El detalle se edita dentro de la venta y se guarda en la misma base Supabase
    # mediante el ORM, sin que el administrador tenga que cambiar de pantalla.
    model = VentaDetalle
    extra = 1
    fields = ('producto', 'talla', 'cantidad', 'subtotal')
    readonly_fields = ('subtotal',)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    inlines = (VentaDetalleInline,)
    change_list_template = 'admin/inventario/venta/change_list.html'
    list_display = ('id', 'fecha', 'cliente', 'rut_cliente', 'total')
    list_filter = ('fecha',)
    date_hierarchy = 'fecha'
    search_fields = ('rut_cliente', 'cliente__rut', 'cliente__nombre')
    ordering = ('-fecha',)

    def get_queryset(self, request):
        # El rango se aplica al queryset antes de contar o sumar, por lo que el
        # reporte representa exactamente el periodo seleccionado.
        queryset = super().get_queryset(request)
        fecha_desde = parse_date(request.GET.get('fecha_desde', ''))
        fecha_hasta = parse_date(request.GET.get('fecha_hasta', ''))
        if fecha_desde:
            queryset = queryset.filter(fecha__date__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__date__lte=fecha_hasta)
        return queryset

    def changelist_view(self, request, extra_context=None):
        # Sum y count son agregaciones SQL ejecutadas por Django sobre Supabase.
        queryset = self.get_queryset(request)
        resumen = queryset.aggregate(
            total_ventas=Sum('total'),
        )
        contexto = {
            'fecha_desde': request.GET.get('fecha_desde', ''),
            'fecha_hasta': request.GET.get('fecha_hasta', ''),
            'total_ventas_periodo': resumen['total_ventas'] or 0,
            'cantidad_ventas_periodo': queryset.count(),
        }
        if extra_context:
            contexto.update(extra_context)
        return super().changelist_view(request, extra_context=contexto)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalcular_total()
