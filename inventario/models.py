from django.db import models

# Create your models here.
class Producto(models.Model):
    nombre = models.CharField(max_length=64)
    codigo = models.CharField(max_length=50, unique=True, null=True)
    precio = models.PositiveIntegerField(default=0)
    descripcion = models.CharField(max_length=128, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)


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


class VentaDetalle(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
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
        self.subtotal = self.cantidad * self.producto.precio
        super().save(*args, **kwargs)