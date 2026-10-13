from django import forms
from .models import Cliente, Producto, ProductoTalla

TALLAS_VALIDAS = {str(talla) for talla in range(35, 47)}

class ProductoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.codigo} - {obj.nombre}'


class ProductoForm(forms.ModelForm):
    tallas = forms.CharField(
        required=False,
        label='Stock por talla',
        help_text='Selecciona una talla y define cuantas unidades tienes disponibles.',
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['tallas'].initial = ','.join(
                f'{talla.talla}:{talla.stock}'
                for talla in self.instance.tallas.all()
            )

    class Meta:
        model = Producto
        fields = ['nombre', 'codigo', 'precio', 'descripcion', 'stock', 'activo']
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

    def clean_tallas(self):
        valor = self.cleaned_data['tallas'].strip()
        tallas = {}
        if not valor:
            return tallas
        for entrada in valor.split(','):
            partes = entrada.strip().split(':', 1)
            if len(partes) != 2 or not partes[0].strip():
                raise forms.ValidationError('Usa el formato talla:stock, por ejemplo S:10, M:5.')
            talla = partes[0].strip()
            if talla not in TALLAS_VALIDAS:
                raise forms.ValidationError('La talla debe estar entre 35 y 46.')
            try:
                stock = int(partes[1].strip())
            except ValueError:
                raise forms.ValidationError('El stock de cada talla debe ser un número entero.')
            if stock < 0:
                raise forms.ValidationError('El stock por talla no puede ser negativo.')
            if talla in tallas:
                raise forms.ValidationError(f'La talla {talla} está repetida.')
            tallas[talla] = stock
        return tallas


class ProductoTallaForm(forms.ModelForm):
    class Meta:
        model = ProductoTalla
        fields = ['talla', 'stock']


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
    talla = forms.ModelChoiceField(
        queryset=ProductoTalla.objects.select_related('producto').all(),
        required=False,
        label='Talla',
        empty_label='Producto sin talla / stock general',
        widget=forms.Select(attrs={'data-talla-selector': 'true'}),
    )
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.filter(activo=True)
        self.fields['talla'].queryset = ProductoTalla.objects.filter(stock__gt=0).select_related('producto')

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
        talla = cleaned_data.get('talla')
        cantidad = cleaned_data.get('cantidad')
        if talla and producto and talla.producto_id != producto.pk:
            self.add_error('talla', 'La talla seleccionada no pertenece al producto.')
        if producto and producto.tallas.exists() and not talla:
            self.add_error('talla', 'Selecciona una talla para este producto.')
        stock_disponible = talla.stock if talla else (producto.stock if producto else 0)
        if cantidad is not None and cantidad < 1:
            self.add_error('cantidad', 'La cantidad debe ser al menos 1.')
        if producto and cantidad and cantidad > stock_disponible:
            self.add_error('cantidad', f'Solo hay {stock_disponible} unidades disponibles.')

        if cleaned_data.get('cliente_habitual'):
            required_fields = ('nombre', 'telefono', 'direccion', 'correo')
            for field_name in required_fields:
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, 'Completa este dato para guardar el cliente habitual.')
        return cleaned_data

