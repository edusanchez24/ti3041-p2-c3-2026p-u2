from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('inventario', '0007_producto_activo_producto_talla'),
    ]

    operations = [
        migrations.AddField(
            model_name='ventadetalle',
            name='talla',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='inventario.productotalla',
            ),
        ),
    ]
