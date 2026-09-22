import django.db.models.deletion
from django.db import migrations, models


def migrar_ventas_existentes(apps, schema_editor):
    Venta = apps.get_model('inventario', 'Venta')
    VentaDetalle = apps.get_model('inventario', 'VentaDetalle')

    for venta in Venta.objects.all().iterator():
        if venta.producto_id is not None:
            VentaDetalle.objects.create(
                venta_id=venta.pk,
                producto_id=venta.producto_id,
                cantidad=venta.cantidad,
                subtotal=venta.total,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0005_venta_cantidad_minima_uno'),
    ]

    operations = [
        migrations.CreateModel(
            name='VentaDetalle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField()),
                ('subtotal', models.PositiveIntegerField(default=0)),
                ('producto', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventario.producto')),
                ('venta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='inventario.venta')),
            ],
        ),
        migrations.RunPython(migrar_ventas_existentes, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name='venta',
            name='venta_cantidad_minima_uno',
        ),
        migrations.RemoveField(
            model_name='venta',
            name='producto',
        ),
        migrations.RemoveField(
            model_name='venta',
            name='cantidad',
        ),
        migrations.AddConstraint(
            model_name='ventadetalle',
            constraint=models.CheckConstraint(
                condition=models.Q(('cantidad__gte', 1)),
                name='venta_detalle_cantidad_minima_uno',
            ),
        ),
    ]