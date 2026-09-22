from django import forms
from .models import Cliente, Producto

class ProductoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.codigo} - {obj.nombre}'


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'codigo', 'precio', 'descripcion', 'stock']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border border-slate-300 bg-white/80 px-3 py-2.5 text-slate-950 shadow-sm outline-none transition duration-200 placeholder:text-slate-400 hover:border-slate-400 focus:border-sky-600 focus:bg-white focus:ring-4 focus:ring-sky-100',
                'placeholder': 'Ej. Auriculares inalambricos',
                'autocomplete': 'off',
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border border-slate-300 bg-white/80 px-3 py-2.5 text-slate-950 shadow-sm outline-none transition duration-200 placeholder:text-slate-400 hover:border-slate-400 focus:border-sky-600 focus:bg-white focus:ring-4 focus:ring-sky-100',
                'placeholder': 'Ej. AUD-001',
                'autocomplete': 'off',
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'w-full rounded-xl border border-slate-300 bg-white/80 px-3 py-2.5 text-slate-950 shadow-sm outline-none transition duration-200 placeholder:text-slate-400 hover:border-slate-400 focus:border-sky-600 focus:bg-white focus:ring-4 focus:ring-sky-100',
                'placeholder': '0',
                'min': '0',
                'inputmode': 'numeric',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'min-h-28 w-full resize-y rounded-xl border border-slate-300 bg-white/80 px-3 py-2.5 text-slate-950 shadow-sm outline-none transition duration-200 placeholder:text-slate-400 hover:border-slate-400 focus:border-sky-600 focus:bg-white focus:ring-4 focus:ring-sky-100',
                'placeholder': 'Describe el producto brevemente',
                'rows': 4,
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'w-full rounded-xl border border-slate-300 bg-white/80 px-3 py-2.5 text-slate-950 shadow-sm outline-none transition duration-200 placeholder:text-slate-400 hover:border-slate-400 focus:border-sky-600 focus:bg-white focus:ring-4 focus:ring-sky-100',
                'placeholder': '0',
                'min': '0',
                'inputmode': 'numeric',
            }),
        }


class VentaForm(forms.Form):
    # Este formulario concentra los datos de la venta y del cliente ocasional o habitual.
    cliente_habitual = forms.BooleanField(required=False, label='Guardar como cliente habitual')
    nombre = forms.CharField(
        required=False,
        max_length=128,
        widget=forms.TextInput(attrs={'pattern': r'[A-Za-zÁÉÍÓÚáéíóúÑñÜü]+(?:\s+[A-Za-zÁÉÍÓÚáéíóúÑñÜü]+)*'}),
    )
    telefono = forms.CharField(
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={'inputmode': 'numeric', 'pattern': r'[0-9]+'}),
    )
    direccion = forms.CharField(required=False, max_length=200)
    correo = forms.EmailField(required=False)
    producto = ProductoChoiceField(queryset=Producto.objects.all(), label='Producto')
    cantidad = forms.IntegerField(
        min_value=1,
        error_messages={'min_value': 'La cantidad debe ser al menos 1.'},
        label='Cantidad',
        widget=forms.NumberInput(attrs={'min': '1', 'inputmode': 'numeric'}),
    )

    rut_cliente = forms.RegexField(
        regex=r'^\d{1,10}-[\dKk]$',
        max_length=12,
        required=True,
        label='RUT del cliente',
        widget=forms.TextInput(attrs={
            'placeholder': '12345678-9',
            'autocomplete': 'off',
            'pattern': r'[0-9]{1,10}-[0-9Kk]',
        }),
    )

    def clean_nombre(self):
        # La validación del servidor protege el flujo aunque se desactive la validación HTML.
        nombre = self.cleaned_data['nombre'].strip()
        if nombre and not all(parte.isalpha() for parte in nombre.split()):
            raise forms.ValidationError('El nombre solo puede contener letras y espacios.')
        return nombre

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono'].strip()
        if telefono and not telefono.isdecimal():
            raise forms.ValidationError('El teléfono solo puede contener números.')
        return telefono

    def clean(self):
        # Las reglas de stock se validan antes de guardar para evitar cantidades imposibles.
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')
        if cantidad is not None and cantidad < 1:
            self.add_error('cantidad', 'La cantidad debe ser al menos 1.')
        if producto and cantidad and cantidad > producto.stock:
            self.add_error('cantidad', f'El producto solo tiene {producto.stock} unidades disponibles.')

        if cleaned_data.get('cliente_habitual'):
            required_fields = ('nombre', 'telefono', 'direccion', 'correo')
            for field_name in required_fields:
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, 'Completa este dato para guardar el cliente habitual.')
        return cleaned_data

