import datetime
import time

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.messages import get_messages

from datetime import timedelta
from app.models import Event, User, Category, Venue, Ticket

class BaseEventTestCase(TestCase):
    """Clase base con la configuración común para todos los tests de eventos"""

    def setUp(self):
        # Crear un usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        # Crear un usuario regular
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@test.com",
            password="password123",
            is_organizer=False,
        )

        self.category = Category.objects.create(name='Musica', description='Descripcion ejemplo')
        self.venue = Venue.objects.create(name='Estadio Único', city='La Plata', address='Av. 32', capacity=1000, contact='example')

        # Crear algunos eventos de prueba
        self.event1 = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            category=self.category,
            venue=self.venue,
            state = "AVAILABLE"
        )

        self.event2 = Event.objects.create(
            title="Evento 2",
            description="Descripción del evento 2",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.organizer,
            category=self.category,
            venue=self.venue,
            state = "CANCELLED"
        )

        # Cliente para hacer peticiones
        self.client = Client()


class EventsListViewTest(BaseEventTestCase):
    """Tests para la vista de listado de eventos"""

    def test_events_view_with_login(self):
        """Test que verifica que la vista events funciona cuando el usuario está logueado"""
        # Login con usuario regular
        self.client.login(username="regular", password="password123")

        # Hacer petición a la vista events
        response = self.client.get(reverse("events"))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/events.html")
        self.assertIn("events", response.context)
        self.assertIn("user_is_organizer", response.context)
        self.assertEqual(len(response.context["events"]), 2)
        self.assertFalse(response.context["user_is_organizer"])

        # Verificar que los eventos están ordenados por fecha
        events = list(response.context["events"])
        self.assertEqual(events[0].id, self.event1.id)
        self.assertEqual(events[1].id, self.event2.id)

    def test_events_view_with_organizer_login(self):
        """Test que verifica que la vista events funciona cuando el usuario es organizador"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Hacer petición a la vista events
        response = self.client.get(reverse("events"))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user_is_organizer"])

    def test_events_view_without_login(self):
        """Test que verifica que la vista events redirige a login cuando el usuario no está logueado"""
        # Hacer petición a la vista events sin login
        response = self.client.get(reverse("events"))

        # Verificar que redirecciona al login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))
        
    def test_events_buy_tickets_with_invalid_state(self):
        """Test que verifica que se redirige al usuario cuando intenta comprar tickets de un evento con estado: Cancelado, Agotado o Terminado"""
        self.client.login(username="regular", password="password123")
        response = self.client.get(reverse("events"))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse("ticket_form", args=[self.event2.id]), follow=True)
        
        self.assertRedirects(response, reverse("events"))
        
        # Verifica que se muestra un mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("no se puede realizar la compra" in m.message.lower() for m in messages))
        
    def test_cannot_edit_cancelled_event(self):
        """Test que verifica que se evita al organizador editar un evento que ya fue cancelado"""
        self.client.login(username="organizador", password="password123")

        response = self.client.get(reverse("events"))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse("event_edit", args=[self.event2.id]), follow=True)
        
        self.assertRedirects(response, reverse("events"))
        
        # Verifica que se muestra un mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("no se puede modificar" in m.message.lower() for m in messages))    

class EventDetailViewTest(BaseEventTestCase):
    """Tests para la vista de detalle de un evento"""

    def test_event_detail_view_with_login(self):
        """Test que verifica que la vista event_detail funciona cuando el usuario está logueado"""
        # Login con usuario regular
        self.client.login(username="regular", password="password123")

        # Hacer petición a la vista event_detail
        response = self.client.get(reverse("event_detail", args=[self.event1.id]))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event_detail.html")
        self.assertIn("event", response.context)
        self.assertEqual(response.context["event"].id, self.event1.id)

    def test_event_detail_view_without_login(self):
        """Test que verifica que la vista event_detail redirige a login cuando el usuario no está logueado"""
        # Hacer petición a la vista event_detail sin login
        response = self.client.get(reverse("event_detail", args=[self.event1.id]))

        # Verificar que redirecciona al login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_event_detail_view_with_invalid_id(self):
        """Test que verifica que la vista event_detail devuelve 404 cuando el evento no existe"""
        # Login con usuario regular
        self.client.login(username="regular", password="password123")

        # Hacer petición a la vista event_detail con ID inválido
        response = self.client.get(reverse("event_detail", args=[999]))

        # Verificar respuesta
        self.assertEqual(response.status_code, 404)
    
    def test_event_detail_view_cuenta_regresiva_regular_user_evento_futuro(self):
        self.client.login(username="regular", password="password123")
        response = self.client.get(reverse("event_detail", args=[self.event2.id]))
        self.assertEqual(response.status_code, 200)
        cuenta_regresiva = response.context["cuenta_regresiva"]
        self.assertIsNotNone(cuenta_regresiva)
        self.assertRegex(cuenta_regresiva, r'1 dias, 23 horas, 59 minutos')

    def test_event_detail_view_cuenta_regresiva_no_organizador(self):
        self.client.login(username="organizador", password="password123")
        response = self.client.get(reverse("event_detail", args=[self.event1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['cuenta_regresiva'])

    def test_event_detail_view_cuenta_regresiva_evento_pasado(self):
        evento_pasado = Event.objects.create(
            title="Evento pasado",
            description="Evento que ya ha ocurrido",
            scheduled_at=timezone.now() - datetime.timedelta(days=1),
            organizer=self.organizer,
            category=self.category,
            venue=self.venue
        )
        self.client.login(username="regular", password="password123")
        response = self.client.get(reverse("event_detail", args=[evento_pasado.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cuenta_regresiva'], "El evento ya ha ocurrido.")
        
    
        
class EventFormViewTest(BaseEventTestCase):
    """Tests para la vista del formulario de eventos"""

    def test_event_form_view_with_organizer(self):
        """Test que verifica que la vista event_form funciona cuando el usuario es organizador"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Hacer petición a la vista event_form para crear nuevo evento (id=None)
        response = self.client.get(reverse("event_form"))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event_form.html")
        self.assertIn("event", response.context)
        self.assertTrue(response.context["user_is_organizer"])

    def test_event_form_view_with_regular_user(self):
        """Test que verifica que la vista event_form redirige cuando el usuario no es organizador"""
        # Login con usuario regular
        self.client.login(username="regular", password="password123")

        # Hacer petición a la vista event_form
        response = self.client.get(reverse("event_form"))

        # Verificar que redirecciona a events
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events"))

    def test_event_form_view_without_login(self):
        """Test que verifica que la vista event_form redirige a login cuando el usuario no está logueado"""
        # Hacer petición a la vista event_form sin login
        response = self.client.get(reverse("event_form"))

        # Verificar que redirecciona al login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_event_form_edit_existing(self):
        """Test que verifica que se puede editar un evento existente"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Hacer petición a la vista event_form para editar evento existente
        response = self.client.get(reverse("event_edit", args=[self.event1.id]))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event_form.html")
        self.assertEqual(response.context["event"].id, self.event1.id)


class EventFormSubmissionTest(BaseEventTestCase):
    """Tests para la creación y edición de eventos mediante POST"""

    def test_event_form_post_create(self):
        """Test que verifica que se puede crear un evento mediante POST"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Crear datos para el evento
        event_data = {
            "title": "Nuevo Evento",
            "description": "Descripción del nuevo evento",
            "date": "2025-05-01",
            "time": "14:30",
            "categoria": str(self.category.id),
            "venue": str(self.venue.id), 
            "state": "AVAILABLE"
        }

        # Hacer petición POST a la vista event_form
        response = self.client.post(reverse("event_form"), data=event_data)

        # Verificar que redirecciona a events
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events"))

        # Verificar que se creó el evento
        self.assertTrue(Event.objects.filter(title="Nuevo Evento").exists())
        evento = Event.objects.get(title="Nuevo Evento")
        self.assertEqual(evento.description, "Descripción del nuevo evento")
        self.assertEqual(evento.scheduled_at.year, 2025)
        self.assertEqual(evento.scheduled_at.month, 5)
        self.assertEqual(evento.scheduled_at.day, 1)
        self.assertEqual(evento.scheduled_at.hour, 14)
        self.assertEqual(evento.scheduled_at.minute, 30)
        self.assertEqual(evento.organizer, self.organizer)

    def test_event_form_post_edit(self):
        """Test que verifica que se puede editar un evento existente mediante POST"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Datos para actualizar el evento
        updated_data = {
            "title": "Evento 1 Actualizado",
            "description": "Nueva descripción actualizada",
            "date": "2025-06-15",
            "time": "16:45",
            "categoria": str(self.category.id),
            "venue": str(self.venue.id)
        }

        # Hacer petición POST para editar el evento
        response = self.client.post(reverse("event_edit", args=[self.event1.id]), updated_data)

        # Verificar que redirecciona a events
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events"))

        # Verificar que el evento fue actualizado
        self.event1.refresh_from_db()

        self.assertEqual(self.event1.title, "Evento 1 Actualizado")
        self.assertEqual(self.event1.description, "Nueva descripción actualizada")
        self.assertEqual(self.event1.scheduled_at.year, 2025)
        self.assertEqual(self.event1.scheduled_at.month, 6)
        self.assertEqual(self.event1.scheduled_at.day, 15)
        self.assertEqual(self.event1.scheduled_at.hour, 16)
        self.assertEqual(self.event1.scheduled_at.minute, 45)


class EventDeleteViewTest(BaseEventTestCase):
    """Tests para la eliminación de eventos"""

    def test_event_delete_with_organizer(self):
        """Test que verifica que un organizador puede eliminar un evento"""
        # Iniciar sesión como organizador
        self.client.login(username="organizador", password="password123")

        # Verificar que el evento existe antes de eliminar
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

        # Hacer una petición POST para eliminar el evento
        response = self.client.post(reverse("event_delete", args=[self.event1.id]))

        # Verificar que redirecciona a la página de eventos
        self.assertRedirects(response, reverse("events"))

        # Verificar que el evento ya no existe
        self.assertFalse(Event.objects.filter(pk=self.event1.id).exists())

    def test_event_delete_with_regular_user(self):
        """Test que verifica que un usuario regular no puede eliminar un evento"""
        # Iniciar sesión como usuario regular
        self.client.login(username="regular", password="password123")

        # Verificar que el evento existe antes de intentar eliminarlo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

        # Hacer una petición POST para intentar eliminar el evento
        response = self.client.post(reverse("event_delete", args=[self.event1.id]))

        # Verificar que redirecciona a la página de eventos sin eliminar
        self.assertRedirects(response, reverse("events"))

        # Verificar que el evento sigue existiendo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

    def test_event_delete_with_get_request(self):
        """Test que verifica que la vista redirecciona si se usa GET en lugar de POST"""
        # Iniciar sesión como organizador
        self.client.login(username="organizador", password="password123")

        # Hacer una petición GET para intentar eliminar el evento
        response = self.client.get(reverse("event_delete", args=[self.event1.id]))

        # Verificar que redirecciona a la página de eventos
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event_delete.html")

        # Verificar que el evento sigue existiendo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

    def test_event_delete_nonexistent_event(self):
        """Test que verifica el comportamiento al intentar eliminar un evento inexistente"""
        # Iniciar sesión como organizador
        self.client.login(username="organizador", password="password123")

        # ID inexistente
        nonexistent_id = 9999

        # Verificar que el evento con ese ID no existe
        self.assertFalse(Event.objects.filter(pk=nonexistent_id).exists())

        # Hacer una petición POST para eliminar el evento inexistente
        response = self.client.post(reverse("event_delete", args=[nonexistent_id]))

        # Verificar que devuelve error 404
        self.assertEqual(response.status_code, 404)

    def test_event_delete_without_login(self):
        """Test que verifica que la vista redirecciona a login si el usuario no está autenticado"""
        # Verificar que el evento existe antes de intentar eliminarlo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

        # Hacer una petición POST sin iniciar sesión
        response = self.client.post(reverse("event_delete", args=[self.event1.id]))

        # Verificar que redirecciona al login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

        # Verificar que el evento sigue existiendo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())
        
#simula la creación de un ticket a través de la view y verificar que no se permite cuando el evento está lleno       
class TicketIntegrationTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username='organizer', password='12345')
        self.user = User.objects.create_user(username='testuser', password='12345')
        
        # Crear categoría válida
        self.category = Category.objects.create(name="Concierto")

        # Crear lugar válido (Venue)
        self.venue = Venue.objects.create(
            name="Auditorio Central",
            address="Calle Falsa 123",
            capacity=100
        )
        self.event = Event.objects.create(
            title="Evento lleno", 
            general_capacity=2, 
            vip_capacity=0, 
            description="Evento para test", 
            scheduled_at=timezone.now() + timedelta(days=1),
            organizer=self.organizer,
            category=self.category,  # Necesitas un objeto Category válido
            venue=self.venue  # Necesitas un objeto Venue válido
        )
        # Crear tickets para llenar el evento
        Ticket.objects.create(user=self.user, event=self.event, quantity=1, type='GENERAL')
        Ticket.objects.create(user=self.user, event=self.event, quantity=1, type='GENERAL')

    def test_cannot_purchase_when_capacity_reached(self):
        self.client.login(username='testuser', password='12345')
        url = reverse('ticket_form', args=[self.event.id])
        response = self.client.post(url, {
        'quantity': 1,
        'type': 'GENERAL'
        })
        self.assertContains(response, "No hay mas cupo disponible", status_code=200)


class FutureEventsViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='organizer', password='pass123')
        self.user.is_organizer = True
        self.user.save()

        self.category = Category.objects.create(name='Conciertos')
        self.venue = Venue.objects.create(
            name='Estadio Central',
            city='Ciudad',
            address='Calle 123',
            capacity=1000,
            contact='contacto@venue.com'
        )

        # Evento pasado
        self.past_event = Event.objects.create(
            title='Evento Pasado',
            description='Evento que ya pasó',
            scheduled_at=timezone.now() - timedelta(days=5),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )

        # Evento futuro
        self.future_event = Event.objects.create(
            title='Evento Futuro',
            description='Evento que será',
            scheduled_at=timezone.now() + timedelta(days=5),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )

    def test_only_future_events_are_listed(self):
        self.client.login(username='organizer', password='pass123')

        url = reverse('events')  # Cambia 'events-list' por el nombre correcto de tu url
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Comprobar que el evento futuro está en la respuesta
        self.assertContains(response, self.future_event.title)

        # Comprobar que el evento pasado NO está en la respuesta
        self.assertNotContains(response, self.past_event.title)