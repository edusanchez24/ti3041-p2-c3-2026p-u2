from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Cliente, Producto, Venta, VentaDetalle
from .forms import ProductoForm, VentaForm

from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET

# Create your views here.
def producto_list(request):
    # El catálogo filtra en la base de datos para no cargar productos innecesarios en la vista.
    filtro_stock = request.GET.get('stock', 'todos')
    filtros_validos = {'todos', 'disponibles', 'no_disponibles'}
    if filtro_stock not in filtros_validos:
        filtro_stock = 'todos'

    productos = Producto.objects.order_by('nombre')
    if filtro_stock == 'disponibles':
        productos = productos.filter(stock__gt=0)
    elif filtro_stock == 'no_disponibles':
        productos = productos.filter(stock=0)

    return render(request, 'inventario/producto_list.html', {
        'object_list': productos,
        'filtro_stock': filtro_stock,
    })

def producto_detail(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'inventario/producto_detail.html', {'object': producto})

@csrf_protect
def producto_create(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('producto_list')
    else:
        form = ProductoForm()

    return render(request, 'inventario/producto_form.html', {'form': form})

@csrf_protect
def producto_update(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)

        if form.is_valid():
            form.save()
            return redirect('producto_list')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'inventario/producto_form.html', {'form': form})

@csrf_protect
def producto_delete(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        producto.delete()
        return redirect('producto_list')

    return render(request, 'inventario/producto_confirm_delete.html', {'object': producto})


def venta_list(request):
    # `icontains` permite encontrar ventas escribiendo solo una parte del RUT.
    rut_busqueda = request.GET.get('rut', '').strip()
    ventas = Venta.objects.select_related('cliente').prefetch_related('detalles__producto').order_by('-fecha')
    if rut_busqueda:
        ventas = ventas.filter(rut_cliente__icontains=rut_busqueda)
    return render(request, 'inventario/venta_list.html', {
        'ventas': ventas,
        'rut_busqueda': rut_busqueda,
    })


@require_GET
def cliente_por_rut(request):
    # Este endpoint alimenta el autocompletado del formulario sin exponer datos innecesarios.
    rut = request.GET.get('rut', '').strip()
    cliente = Cliente.objects.filter(rut=rut).first()
    if cliente is None:
        return JsonResponse({'encontrado': False})
    return JsonResponse({
        'encontrado': True,
        'nombre': cliente.nombre,
        'telefono': cliente.telefono,
        'direccion': cliente.direccion,
        'correo': cliente.correo,
    })


def _venta_carrito(request):
    return request.session.get('venta_carrito', {})


def _venta_carrito_context(request):
    carrito = _venta_carrito(request)
    productos = Producto.objects.filter(pk__in=carrito.keys())
    items = []
    for producto in productos:
        cantidad = carrito[str(producto.pk)]
        items.append({
            'producto': producto,
            'cantidad': cantidad,
            'subtotal': producto.precio * cantidad,
        })
    return {
        'carrito': items,
        'carrito_total': sum(item['subtotal'] for item in items),
    }


def _venta_form_from_session(request):
    datos_cliente = request.session.get('venta_datos_cliente', {})
    return VentaForm(initial=datos_cliente)


@csrf_protect
def venta_create(request):
    accion = request.POST.get('accion') if request.method == 'POST' else None

    if request.method == 'POST' and accion == 'agregar':
        # El carrito y los datos del cliente se conservan en sesión mientras se agregan productos.
        form = VentaForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            cantidad = form.cleaned_data['cantidad']
            carrito = _venta_carrito(request)
            cantidad_total = carrito.get(str(producto.pk), 0) + cantidad
            if cantidad_total > producto.stock:
                form.add_error('cantidad', f'El producto solo tiene {producto.stock} unidades disponibles.')
            else:
                carrito[str(producto.pk)] = cantidad_total
                request.session['venta_carrito'] = carrito
                request.session['venta_datos_cliente'] = {
                    field_name: form.cleaned_data.get(field_name)
                    for field_name in ('rut_cliente', 'cliente_habitual', 'nombre', 'telefono', 'direccion', 'correo')
                }
                request.session.modified = True
                messages.success(request, f'{producto.nombre} agregado a la venta.')
                return redirect('venta_create')
    elif request.method == 'POST' and accion == 'confirmar':
        if not _venta_carrito(request):
            messages.error(request, 'Agrega al menos un producto antes de confirmar la venta.')
            return redirect('venta_create')
        return render(request, 'inventario/venta_form.html', {
            'form': _venta_form_from_session(request),
            'confirmando': True,
            **_venta_carrito_context(request),
        })
    elif request.method == 'POST' and accion == 'registrar':
        # La transacción mantiene sincronizados el stock, el detalle y el total de la venta.
        carrito = _venta_carrito(request)
        datos_cliente = request.session.get('venta_datos_cliente', {})
        if not carrito:
            messages.error(request, 'Agrega al menos un producto antes de confirmar la venta.')
            return redirect('venta_create')

        with transaction.atomic():
            productos = {
                str(producto.pk): producto
                for producto in Producto.objects.select_for_update().filter(pk__in=carrito.keys())
            }
            for producto_id, cantidad in carrito.items():
                producto = productos.get(str(producto_id))
                if producto is None or cantidad < 1 or cantidad > producto.stock:
                    messages.error(request, 'Uno de los productos ya no tiene stock suficiente.')
                    return redirect('venta_create')

            cliente = None
            if datos_cliente.get('cliente_habitual'):
                cliente, _ = Cliente.objects.update_or_create(
                    rut=datos_cliente['rut_cliente'],
                    defaults={
                        'nombre': datos_cliente['nombre'],
                        'telefono': datos_cliente['telefono'],
                        'direccion': datos_cliente['direccion'],
                        'correo': datos_cliente['correo'],
                    },
                )

            venta = Venta.objects.create(
                rut_cliente=datos_cliente['rut_cliente'],
                cliente=cliente,
            )
            total_venta = 0
            for producto_id, cantidad in carrito.items():
                producto = productos[str(producto_id)]
                detalle = VentaDetalle.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                )
                producto.stock -= cantidad
                producto.save(update_fields=['stock'])
                total_venta += detalle.subtotal

            venta.total = total_venta
            venta.save(update_fields=['total'])

        request.session.pop('venta_carrito', None)
        request.session.pop('venta_datos_cliente', None)
        messages.success(request, f'Venta registrada por ${total_venta}.')
        return redirect('venta_list')
    elif request.method == 'POST' and accion == 'eliminar':
        carrito = _venta_carrito(request)
        producto_id = request.POST.get('producto_id')
        carrito.pop(str(producto_id), None)
        request.session['venta_carrito'] = carrito
        request.session.modified = True
        return redirect('venta_create')
    elif request.method == 'POST' and accion == 'volver':
        return redirect('venta_create')
    elif request.method == 'POST' and accion == 'limpiar':
        request.session.pop('venta_carrito', None)
        request.session.pop('venta_datos_cliente', None)
        return redirect('venta_create')
    else:
        form = _venta_form_from_session(request)

    return render(request, 'inventario/venta_form.html', {
        'form': form,
        **_venta_carrito_context(request),
    })