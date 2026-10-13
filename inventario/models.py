from django.db import models

# Create your models here.
class Producto(models.Model):
    nombre = models.CharField(max_length=64)
    codigo = models.CharField(max_length=50, unique=True, null=True)
    precio = models.PositiveIntegerField(default=0)
    descripcion = models.CharField(max_length=128, blank=True, default='')
    stock = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    def actualizar_stock_total(self):
        self.stock = sum(talla.stock for talla in self.tallas.all())
        type(self).objects.filter(pk=self.pk).update(stock=self.stock)
        return self.stock

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class ProductoTalla(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='tallas')
    talla = models.CharField(max_length=20)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('producto', 'talla'),
                name='producto_talla_unica',
            ),
        ]
        ordering = ('talla',)

    def __str__(self):
        return f'{self.producto} - talla {self.talla}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.producto.actualizar_stock_total()

    def delete(self, *args, **kwargs):
        producto = self.producto
        resultado = super().delete(*args, **kwargs)
        producto.actualizar_stock_total()
        return resultado


class Cliente(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=128, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    correo = models.EmailField(blank=True)


class Venta(models.Model):
    rut_cliente = models.CharField(max_length=12, null=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, null=True, blank=True)
    total = models.PositiveIntegerField(default=0)
    fecha = models.DateTimeField(auto_now_add=True)

    def recalcular_total(self):
        self.total = sum(detalle.subtotal for detalle in self.detalles.all())
        type(self).objects.filter(pk=self.pk).update(total=self.total)
        return self.total

    def __str__(self):
        return f'Venta #{self.pk}'


class VentaDetalle(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    talla = models.ForeignKey(ProductoTalla, on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.PositiveIntegerField()
    subtotal = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gte=1),
                name='venta_detalle_cantidad_minima_uno',
            ),
        ]

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.producto.precio if self.producto else 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.producto} x {self.cantidad}'


def actualizar_total_venta(sender, instance, **kwargs):
    if instance.venta_id:
        instance.venta.recalcular_total()


models.signals.post_save.connect(actualizar_total_venta, sender=VentaDetalle)
models.signals.post_delete.connect(actualizar_total_venta, sender=VentaDetalle)