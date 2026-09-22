from django.test import TestCase
from .forms import VentaForm
from .models import Cliente, Producto, Venta, VentaDetalle

# Create your tests here.
class VentaFlowTests(TestCase):
	def setUp(self):
		self.producto = Producto.objects.create(nombre='Teclado', codigo='TEC-001', precio=10000, stock=5)

	def test_venta_ocasional_guarda_rut_total_y_descuenta_stock(self):
		self.client.post('/ventas/nueva/', {
			'accion': 'agregar',
			'rut_cliente': '11111111-1',
			'producto': self.producto.pk,
			'cantidad': 2,
		})
		response = self.client.post('/ventas/nueva/', {'accion': 'registrar'})

		self.assertRedirects(response, '/ventas/')
		venta = Venta.objects.get()
		self.assertEqual(venta.rut_cliente, '11111111-1')
		self.assertIsNone(venta.cliente)
		self.assertEqual(venta.total, 20000)
		self.assertEqual(venta.detalles.get().cantidad, 2)
		self.assertEqual(Producto.objects.get(pk=self.producto.pk).stock, 3)

	def test_venta_puede_guardar_cliente_habitual(self):
		self.client.post('/ventas/nueva/', {
			'accion': 'agregar',
			'rut_cliente': '22222222-2',
			'producto': self.producto.pk,
			'cantidad': 1,
			'cliente_habitual': 'on',
			'nombre': 'Ana Perez',
			'telefono': '56912345678',
			'direccion': 'Av. Central 123',
			'correo': 'ana@example.com',
		})
		response = self.client.post('/ventas/nueva/', {'accion': 'registrar'})

		self.assertRedirects(response, '/ventas/')
		self.assertEqual(Cliente.objects.get(rut='22222222-2').nombre, 'Ana Perez')
		self.assertEqual(Venta.objects.get().cliente.rut, '22222222-2')

	def test_nombre_y_telefono_solo_aceptan_valores_validos(self):
		form = VentaForm(data={
			'rut_cliente': '23333333-3',
			'nombre': 'Ana Perez',
			'telefono': '56912345678',
			'producto': self.producto.pk,
			'cantidad': 1,
		})
		self.assertTrue(form.is_valid())

		form = VentaForm(data={
			'rut_cliente': '23333333-3',
			'nombre': 'Ana Perez2',
			'telefono': '+56912345678',
			'producto': self.producto.pk,
			'cantidad': 1,
		})
		self.assertFalse(form.is_valid())
		self.assertIn('nombre', form.errors)
		self.assertIn('telefono', form.errors)

		form = VentaForm(data={
			'rut_cliente': '12.345.678-9',
			'producto': self.producto.pk,
			'cantidad': 1,
		})
		self.assertFalse(form.is_valid())
		self.assertIn('rut_cliente', form.errors)

	def test_consulta_cliente_por_rut_devuelve_datos(self):
		Cliente.objects.create(
			rut='24444444-4',
			nombre='Luis Soto',
			telefono='999999999',
			direccion='Calle 1',
			correo='luis@example.com',
		)

		respuesta = self.client.get('/clientes/buscar/?rut=24444444-4')

		self.assertEqual(respuesta.status_code, 200)
		self.assertEqual(respuesta.json()['nombre'], 'Luis Soto')
		self.assertEqual(respuesta.json()['telefono'], '999999999')

	def test_selector_de_venta_muestra_codigo_y_nombre(self):
		form = VentaForm()

		self.assertIn('TEC-001 - Teclado', str(form['producto']))

	def test_no_permite_vender_mas_stock_disponible(self):
		response = self.client.post('/ventas/nueva/', {
			'accion': 'agregar',
			'rut_cliente': '33333333-3',
			'producto': self.producto.pk,
			'cantidad': 6,
		})

		self.assertEqual(response.status_code, 200)
		self.assertFalse(Venta.objects.exists())
		self.assertEqual(Producto.objects.get(pk=self.producto.pk).stock, 5)

	def test_no_permite_agregar_cantidad_cero(self):
		response = self.client.post('/ventas/nueva/', {
			'accion': 'agregar',
			'rut_cliente': '44444444-4',
			'producto': self.producto.pk,
			'cantidad': 0,
		})

		self.assertEqual(response.status_code, 200)
		self.assertFalse(Venta.objects.exists())
		self.assertContains(response, 'La cantidad debe ser al menos 1.')

	def test_puede_agregar_varios_productos_y_confirmar_una_venta(self):
		otro_producto = Producto.objects.create(nombre='Mouse', codigo='MOU-001', precio=5000, stock=4)
		cliente_data = {'rut_cliente': '55555555-5'}

		self.client.post('/ventas/nueva/', {
			'accion': 'agregar',
			**cliente_data,
			'producto': self.producto.pk,
			'cantidad': 2,
		})
		self.client.post('/ventas/nueva/', {
			'accion': 'agregar',
			**cliente_data,
			'producto': otro_producto.pk,
			'cantidad': 1,
		})
		confirmacion = self.client.post('/ventas/nueva/', {'accion': 'confirmar'})

		self.assertEqual(confirmacion.status_code, 200)
		self.assertContains(confirmacion, 'Confirmar venta')
		self.assertEqual(Venta.objects.count(), 0)

		respuesta = self.client.post('/ventas/nueva/', {'accion': 'registrar'})

		self.assertRedirects(respuesta, '/ventas/')
		self.assertEqual(Venta.objects.count(), 1)
		self.assertEqual(VentaDetalle.objects.count(), 2)
		self.assertEqual(Venta.objects.get().total, 25000)
		self.assertEqual(Producto.objects.get(pk=self.producto.pk).stock, 3)
		self.assertEqual(Producto.objects.get(pk=otro_producto.pk).stock, 3)

	def test_puede_eliminar_producto_del_carrito(self):
		self.client.post('/ventas/nueva/', {
			'accion': 'agregar',
			'rut_cliente': '66666666-6',
			'producto': self.producto.pk,
			'cantidad': 1,
		})

		respuesta = self.client.post('/ventas/nueva/', {
			'accion': 'eliminar',
			'producto_id': self.producto.pk,
		})

		self.assertRedirects(respuesta, '/ventas/nueva/')
		self.assertNotIn(str(self.producto.pk), self.client.session.get('venta_carrito', {}))

	def test_volver_desde_confirmacion_conserva_productos_y_datos(self):
		self.client.post('/ventas/nueva/', {
			'accion': 'agregar',
			'rut_cliente': '77777777-7',
			'producto': self.producto.pk,
			'cantidad': 1,
			'nombre': 'Luis Soto',
			'telefono': '999999999',
			'direccion': 'Calle 1',
			'correo': 'luis@example.com',
		})
		self.client.post('/ventas/nueva/', {'accion': 'confirmar'})

		respuesta = self.client.post('/ventas/nueva/', {'accion': 'volver'})

		self.assertRedirects(respuesta, '/ventas/nueva/')
		pagina = self.client.get('/ventas/nueva/')
		self.assertContains(pagina, 'Luis Soto')
		self.assertContains(pagina, 'TEC-001 - Teclado')


class ProductoFilterTests(TestCase):
	def setUp(self):
		Producto.objects.create(nombre='Disponible', codigo='DIS-001', precio=1000, stock=2)
		Producto.objects.create(nombre='Agotado', codigo='AGO-001', precio=1000, stock=0)

	def test_muestra_todos_los_productos_por_defecto(self):
		respuesta = self.client.get('/productos/')

		self.assertContains(respuesta, 'Disponible')
		self.assertContains(respuesta, 'Agotado')

	def test_filtra_productos_disponibles(self):
		respuesta = self.client.get('/productos/?stock=disponibles')

		self.assertContains(respuesta, 'DIS-001')
		self.assertNotContains(respuesta, 'AGO-001')

	def test_filtra_productos_no_disponibles(self):
		respuesta = self.client.get('/productos/?stock=no_disponibles')

		self.assertNotContains(respuesta, 'DIS-001')
		self.assertContains(respuesta, 'AGO-001')

	def test_formulario_de_producto_muestra_errores_de_creacion(self):
		respuesta = self.client.post('/productos/nuevo/', {
			'nombre': '',
			'codigo': 'NUE-001',
			'precio': 1000,
			'descripcion': '',
			'stock': 1,
		})

		self.assertEqual(respuesta.status_code, 200)
		self.assertTrue(respuesta.context['form'].errors['nombre'])

	def test_formulario_de_producto_muestra_errores_de_edicion(self):
		producto = Producto.objects.get(codigo='DIS-001')
		respuesta = self.client.post(f'/productos/{producto.pk}/editar/', {
			'nombre': '',
			'codigo': producto.codigo,
			'precio': producto.precio,
			'descripcion': producto.descripcion or '',
			'stock': producto.stock,
		})

		self.assertEqual(respuesta.status_code, 200)
		self.assertTrue(respuesta.context['form'].errors['nombre'])


class VentaFilterTests(TestCase):
	def setUp(self):
		Venta.objects.create(rut_cliente='12345678-9', total=1000)
		Venta.objects.create(rut_cliente='98765432-1', total=2000)

	def test_filtra_ventas_por_coincidencia_parcial_de_rut(self):
		respuesta = self.client.get('/ventas/?rut=3456')

		self.assertContains(respuesta, '12345678-9')
		self.assertNotContains(respuesta, '98765432-1')
		self.assertContains(respuesta, '3456')

	def test_sin_busqueda_muestra_todas_las_ventas(self):
		respuesta = self.client.get('/ventas/')

		self.assertContains(respuesta, '12345678-9')
		self.assertContains(respuesta, '98765432-1')

