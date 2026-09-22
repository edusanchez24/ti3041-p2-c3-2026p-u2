from django.db import migrations, models


def eliminar_ventas_sin_cantidad(apps, schema_editor):
    Venta = apps.get_model('inventario', 'Venta')
    Venta.objects.filter(cantidad=0).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0004_alter_venta_producto'),
    ]

    operations = [
        migrations.RunPython(eliminar_ventas_sin_cantidad, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='venta',
            constraint=models.CheckConstraint(
                condition=models.Q(('cantidad__gte', 1)),
                name='venta_cantidad_minima_uno',
            ),
        ),
    ]