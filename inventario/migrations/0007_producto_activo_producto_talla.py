from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('inventario', '0006_venta_detalle'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE inventario_producto "
                        "ADD COLUMN IF NOT EXISTS activo boolean NOT NULL DEFAULT true"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='producto',
                    name='activo',
                    field=models.BooleanField(default=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name='ProductoTalla',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('talla', models.CharField(max_length=20)),
                ('stock', models.PositiveIntegerField(default=0)),
                (
                    'producto',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='tallas',
                        to='inventario.producto',
                    ),
                ),
            ],
            options={
                'ordering': ('talla',),
                'constraints': [
                    models.UniqueConstraint(
                        fields=('producto', 'talla'),
                        name='producto_talla_unica',
                    ),
                ],
            },
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='producto',
                    name='descripcion',
                    field=models.CharField(blank=True, default='', max_length=128),
                ),
            ],
        ),
    ]
