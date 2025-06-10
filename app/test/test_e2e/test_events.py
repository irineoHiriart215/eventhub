import re
from datetime import datetime, timedelta
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from django.test import TestCase, Client

from app.models import User, Ticket, Event, Category, Venue
from app.test.test_e2e.base import BaseE2ETest
from django.urls import reverse 


from django.test import LiveServerTestCase
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase



class EventBaseTest(BaseE2ETest):
    """Clase base específica para tests de eventos"""

    def setUp(self):
        super().setUp()

        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username="usuario",
            email="usuario@example.com",
            password="password123",
            is_organizer=False,
        )

        # Crear eventos de prueba
        self.category = Category.objects.create(name='Musica', description='Descripcion ejemplo')
        self.venue = Venue.objects.create(name='Estadio Único', city='La Plata', address='Av. 32', capacity=1000, contact='example')
        # Evento 1
        event_date1 = timezone.make_aware(datetime(2025, 10, 10, 10, 10))
        self.event1 = Event.objects.create(
            title="Evento de prueba 1",
            description="Descripción del evento 1",
            scheduled_at=event_date1,
            organizer=self.organizer,
            category=self.category,
            venue=self.venue,
            state="AVAILABLE" 
        )

        # Evento 2
        event_date2 = timezone.make_aware(datetime(2025, 11, 15, 14, 30))
        self.event2 = Event.objects.create(
            title="Evento de prueba 2",
            description="Descripción del evento 2",
            scheduled_at=event_date2,
            organizer=self.organizer,
            category=self.category,
            venue=self.venue,
            state="REPROGRAM"
        )

    def _table_has_event_info(self):
        """Método auxiliar para verificar que la tabla tiene la información correcta de eventos"""
        # Verificar encabezados de la tabla
        headers = self.page.locator("table thead th")
        expect(headers.nth(0)).to_have_text("Título")
        expect(headers.nth(1)).to_have_text("Descripción")
        expect(headers.nth(2)).to_have_text("Estado")
        expect(headers.nth(3)).to_have_text("Recinto")
        expect(headers.nth(4)).to_have_text("Fecha")
        expect(headers.nth(5)).to_have_text("Categoria")
        expect(headers.nth(6)).to_have_text("Acciones")

        # Verificar que los eventos aparecen en la tabla
        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(2)

        # Verificar datos del primer evento
        row0 = rows.nth(0)
        expect(row0.locator("td").nth(0)).to_have_text("Evento de prueba 1")
        expect(row0.locator("td").nth(1)).to_have_text("Descripción del evento 1")
        expect(row0.locator("td").nth(2)).to_have_text("Activo")
        expect(row0.locator("td").nth(3)).to_have_text("Estadio Único")
        expect(row0.locator("td").nth(4)).to_have_text("10 oct 2025, 10:10")
        expect(row0.locator("td").nth(5)).to_have_text("Musica")

        # Verificar datos del segundo evento
        expect(rows.nth(1).locator("td").nth(0)).to_have_text("Evento de prueba 2")
        expect(rows.nth(1).locator("td").nth(1)).to_have_text("Descripción del evento 2")
        expect(rows.nth(1).locator("td").nth(2)).to_have_text("Reprogramado")
        expect(rows.nth(1).locator("td").nth(3)).to_have_text("Estadio Único")
        expect(rows.nth(1).locator("td").nth(4)).to_have_text("15 nov 2025, 14:30")
        expect(rows.nth(1).locator("td").nth(5)).to_have_text("Musica")

    def _table_has_correct_actions(self, user_type):
        """Método auxiliar para verificar que las acciones son correctas según el tipo de usuario"""
        row0 = self.page.locator("table tbody tr").nth(0)

        detail_button = row0.get_by_role("link", name="Ver Detalle")
        edit_button = row0.get_by_role("link", name="Editar")
        delete_form = row0.locator("form")
        buy_tickets_button = row0.get_by_role("link", name="Comprar entradas")

        expect(detail_button).to_be_visible()
        expect(detail_button).to_have_attribute("href", f"/events/{self.event1.id}/")

        if user_type == "organizador":
            expect(edit_button).to_be_visible()
            expect(edit_button).to_have_attribute("href", f"/events/{self.event1.id}/edit/")

            expect(delete_form).to_have_attribute("action", f"/events/{self.event1.id}/delete/")
            expect(delete_form).to_have_attribute("method", "GET")

            delete_button = delete_form.get_by_role("button", name="Eliminar")
            expect(delete_button).to_be_visible()
            
            expect(buy_tickets_button).to_have_count(0)
        else:
            expect(edit_button).to_have_count(0)
            expect(delete_form).to_have_count(0)
            expect(buy_tickets_button).to_be_visible()
            expect(buy_tickets_button).to_have_attribute("href", f"/ticket/create/{self.event1.id}")


class EventAuthenticationTest(EventBaseTest):
    """Tests relacionados con la autenticación y permisos de usuarios en eventos"""

    def test_events_page_requires_login(self):
        """Test que verifica que la página de eventos requiere inicio de sesión"""
        # Cerrar sesión si hay alguna activa
        self.context.clear_cookies()

        # Intentar ir a la página de eventos sin iniciar sesión
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar que redirige a la página de login
        expect(self.page).to_have_url(re.compile(r"/accounts/login/"))


class EventDisplayTest(EventBaseTest):
    """Tests relacionados con la visualización de la página de eventos"""

    def test_events_page_display_as_organizer(self):
        """Test que verifica la visualización correcta de la página de eventos para organizadores"""
        self.login_user("organizador", "password123")
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar el título de la página
        expect(self.page).to_have_title("Eventos")

        # Verificar que existe un encabezado con el texto "Eventos"
        header = self.page.locator("h1")
        expect(header).to_have_text("Eventos")
        expect(header).to_be_visible()

        # Verificar que existe una tabla
        table = self.page.locator("table")
        expect(table).to_be_visible()

        self._table_has_event_info()
        self._table_has_correct_actions("organizador")

    def test_events_page_regular_user(self):
        """Test que verifica la visualización de la página de eventos para un usuario regular"""
        # Iniciar sesión como usuario regular
        self.login_user("usuario", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        expect(self.page).to_have_title("Eventos")

        # Verificar que existe un encabezado con el texto "Eventos"
        header = self.page.locator("h1")
        expect(header).to_have_text("Eventos")
        expect(header).to_be_visible()

        # Verificar que existe una tabla
        table = self.page.locator("table")
        expect(table).to_be_visible()

        self._table_has_event_info()
        self._table_has_correct_actions("regular")

    def test_events_page_no_events(self):
        """Test que verifica el comportamiento cuando no hay eventos"""
        # Eliminar todos los eventos
        Event.objects.all().delete()

        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar que existe un mensaje indicando que no hay eventos
        no_events_message = self.page.locator("text=No hay eventos disponibles")
        expect(no_events_message).to_be_visible()


class EventPermissionsTest(EventBaseTest):
    """Tests relacionados con los permisos de usuario para diferentes funcionalidades"""

    def test_buttons_visible_only_for_organizer(self):
        """Test que verifica que los botones de gestión solo son visibles para organizadores"""
        # Primero verificar como organizador
        self.login_user("organizador", "password123")
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar que existe el botón de crear
        create_button = self.page.get_by_role("link", name="Crear Evento")
        expect(create_button).to_be_visible()

        # Cerrar sesión
        self.page.get_by_role("button", name="Salir").click()

        # Iniciar sesión como usuario regular
        self.login_user("usuario", "password123")
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar que NO existe el botón de crear
        create_button = self.page.get_by_role("link", name="Crear Evento")
        expect(create_button).to_have_count(0)


class EventCRUDTest(EventBaseTest):
    """Tests relacionados con las operaciones CRUD (Crear, Leer, Actualizar, Eliminar) de eventos"""

    def test_create_new_event_organizer(self):
        """Test que verifica la funcionalidad de crear un nuevo evento para organizadores"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Hacer clic en el botón de crear evento
        self.page.get_by_role("link", name="Crear Evento").click()

        # Verificar que estamos en la página de creación de evento
        expect(self.page).to_have_url(f"{self.live_server_url}/events/create/")

        header = self.page.locator("h1")
        expect(header).to_have_text("Crear evento")
        expect(header).to_be_visible()

        # Completar el formulario
        self.page.get_by_label("Título del Evento").fill("Evento de prueba E2E")
        self.page.get_by_label("Descripción").fill("Descripción creada desde prueba E2E")
        self.page.get_by_label("Fecha").fill("2026-08-15")
        self.page.get_by_label("Hora").fill("16:45")
        self.page.select_option("select[name='venue']", label="Estadio Único")
        self.page.get_by_label("Musica").check()
        self.page.select_option("select[name='state']", label="Activo")

        # Enviar el formulario
        self.page.get_by_role("button", name="Crear Evento").click()

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Verificar que ahora hay 3 eventos
        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(3)

        row = self.page.locator("table tbody tr").last
        expect(row.locator("td").nth(0)).to_have_text("Evento de prueba E2E")
        expect(row.locator("td").nth(1)).to_have_text("Descripción creada desde prueba E2E")
        expect(row.locator("td").nth(2)).to_have_text("Activo")
        expect(row.locator("td").nth(3)).to_have_text("Estadio Único")
        expect(row.locator("td").nth(4)).to_have_text("15 ago 2026, 16:45")
        expect(row.locator("td").nth(5)).to_have_text("Musica")


    def test_edit_event_organizer(self):
        """Test que verifica la funcionalidad de editar un evento para organizadores"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Hacer clic en el botón editar del primer evento
        self.page.get_by_role("link", name="Editar").first.click()

        # Verificar que estamos en la página de edición
        expect(self.page).to_have_url(f"{self.live_server_url}/events/{self.event1.id}/edit/")

        header = self.page.locator("h1")
        expect(header).to_have_text("Editar evento")
        expect(header).to_be_visible()

        # Verificar que el formulario está precargado con los datos del evento y luego los editamos
        title = self.page.get_by_label("Título del Evento")
        expect(title).to_have_value("Evento de prueba 1")
        title.fill("Titulo editado")

        description = self.page.get_by_label("Descripción")
        expect(description).to_have_value("Descripción del evento 1")
        description.fill("Descripcion Editada")

        selected_option = self.page.locator("select[name='venue'] option:checked")
        expect(selected_option).to_have_text("Estadio Único")

        date = self.page.get_by_label("Fecha")
        expect(date).to_have_value("2025-10-10")
        date.fill("2025-08-20")

        time = self.page.get_by_label("Hora")
        expect(time).to_have_value("10:10")
        time.fill("03:00")

        expect(self.page.get_by_label("Musica")).to_be_checked()
        
        selected_option = self.page.locator("select[name='state'] option:checked")
        expect(selected_option).to_have_text("Activo")
        self.page.select_option("select[name='state']", label="Reprogramado")

        # Enviar el formulario
        self.page.get_by_role("button", name="Editar Evento").click()

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Verificar que el título del evento ha sido actualizado
        row = self.page.locator("table tbody tr").first
        expect(row.locator("td").nth(0)).to_have_text("Titulo editado")
        expect(row.locator("td").nth(1)).to_have_text("Descripcion Editada")
        expect(row.locator("td").nth(2)).to_have_text("Reprogramado")
        expect(row.locator("td").nth(3)).to_have_text("Estadio Único")
        expect(row.locator("td").nth(4)).to_have_text("20 ago 2025, 03:00")
        expect(row.locator("td").nth(5)).to_have_text("Musica")

    def test_delete_event_organizer(self):
        """Test que verifica la funcionalidad de eliminar un evento para organizadores"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")
        self.page.goto(f"{self.live_server_url}/events/")

        # Contar eventos antes de eliminar
        initial_count = len(self.page.locator("table tbody tr").all())

        # Hacer clic en el botón eliminar del primer evento
        self.page.get_by_title("Eliminar").first.click()
        
        self.page.get_by_role("button", name="Sí, eliminar").click()

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Verificar que ahora hay un evento menos
        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(initial_count - 1)

        # Verificar que el evento eliminado ya no aparece en la tabla
        expect(self.page.get_by_text("Evento de prueba 1")).to_have_count(0)

class FutureEventsEndToEndTest(LiveServerTestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='organizer', password='pass123') 
        organizer_group, created = Group.objects.get_or_create(name='Organizers')
        self.user.groups.add(organizer_group)
        self.user.save()

        self.category = Category.objects.create(name='Conciertos')
        self.venue = Venue.objects.create(
            name='Estadio Central',
            city='Ciudad',
            address='Calle 123',
            capacity=1000,
            contact='contacto@venue.com'
        )

        self.past_event = Event.objects.create(
            title='Evento Pasado',
            description='Evento que ya pasó',
            scheduled_at=timezone.now() - timedelta(days=3),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )

        self.future_event = Event.objects.create(
            title='Evento Futuro',
            description='Evento que será',
            scheduled_at=timezone.now() + timedelta(days=3),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )

    def test_authenticated_user_sees_only_future_events(self):
        self.client.login(username='organizer', password='pass123')

        url = reverse('events')  
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.future_event.title)
        self.assertNotContains(response, self.past_event.title)

class EventDetailViewTest(EventBaseTest):
    """Test que verifica la visualización de la página de detalle de eventos para un usuario regular"""
    def test_event_detail_page_regular_user(self):

        event_date3 = timezone.make_aware(datetime(2025, 7, 15, 13, 10))
        self.event3 = Event.objects.create(
            title="Evento de prueba 3",
            description="Evento Futuro",
            scheduled_at=event_date3,
            organizer=self.organizer,
            category=self.category,
            venue=self.venue
        )
        self.login_user("usuario", "password123")
        self.page.goto(f"{self.live_server_url}/events/{self.event3.id}/")
        cuenta_regresiva = self.page.get_by_test_id("cuenta_regresiva")
        expect(cuenta_regresiva).to_have_text(re.compile(r"\d+ dias, \d+ horas, \d+ minutos"))
        
    def test_event_detail_display_event(self):
        """Test que verifica que se muestra bien el estado de un evento especifico"""
        self.login_user("usuario", "password123")
        self.page.goto(f"{self.live_server_url}/events/{self.event1.id}/")
        state = self.page.get_by_test_id("state")
        expect(state).to_be_visible()
        expect(state).to_have_text("Activo")

class TicketEndToEndCapacityTest(StaticLiveServerTestCase):
    def setUp(self):

        self.client = Client()

        # Usuario organizador (NO se loguea con este)
        self.organizer = User.objects.create_user(username="organizer", password="pass123")

        # Crear usuario y loguearlo
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.client.login(username="testuser", password="password123")

        # Crear categoría y venue
        self.category = Category.objects.create(name="Concierto")
        self.venue = Venue.objects.create(
            name="Teatro Principal",
            city="Centro",
            address="Calle Falsa 123",
            capacity=100,
            contact="1234-5678"
        )

        # Crear evento con capacidad agotada
        self.event = Event.objects.create(
            title="Evento lleno",
            description="No hay mas cupo disponible",
            scheduled_at=timezone.now() + timedelta(days=1),
            organizer=self.user,
            category=self.category,
            venue=self.venue,
            general_capacity=2,
            vip_capacity=0,
            state="SOLD_OUT"
        )

        # Crear tickets para agotar el cupo GENERAL
        Ticket.objects.create(event=self.event, user=self.user, type="GENERAL", quantity=2)

    def test_no_se_puede_comprar_si_no_hay_cupo(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Iniciar sesión
            page.goto(self.live_server_url + "/accounts/login/")
            page.fill('input[name="username"]', 'testuser')
            page.fill('input[name="password"]', 'password123')
            page.click('button[type="submit"]')

            # Esperar a que cargue la página de eventos después del login
            page.wait_for_url("**/events/")

            # Intentar acceder a la página de compra del ticket
            page.goto(self.live_server_url + f"/ticket/create/{self.event.id}")
            page.wait_for_url("**/events/")

            # Verificar que no aparece el formulario de compra
            try:
                page.wait_for_selector('select[name="type"]', timeout=5000)
                assert False, "El formulario se mostró para un evento sin cupo"
            except Exception:
                pass  # Esperado que no aparezca el formulario

             # Verificar mensaje de error correcto
            page.wait_for_selector("div.alert-danger:has-text('No se puede realizar la compra porque el evento está Agotado.')", timeout=5000)
           
            # Confirmar que no redirigió al listado de tickets
            assert "/tickets/" not in page.url

            browser.close()
        