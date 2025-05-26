import datetime

from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
import datetime
from app.models import Event, User, Category, Venue, Venue, Category


class EventModelTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )
        self.category = Category.objects.create(name='Música', description='Descripcion ejemplo')
        self.venue = Venue.objects.create(name='Estadio Único', city='La Plata', address='Av. 32', capacity=1000, contact='example')

    def test_event_creation(self):
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            category=self.category,
            state="AVAILABLE"
            category=self.category,
            venue=self.venue
        )
        
        """Test que verifica la creación correcta de eventos"""
        self.assertEqual(event.title, "Evento de prueba")
        self.assertEqual(event.description, "Descripción del evento de prueba")
        self.assertEqual(event.organizer, self.organizer)
        self.assertEqual(event.venue, self.venue)
        self.assertEqual(event.category, self.category)
        self.assertEqual(event.state, "AVAILABLE")
        self.assertIsNotNone(event.created_at)
        self.assertIsNotNone(event.updated_at)

    def test_event_validate_with_valid_data(self):
        """Test que verifica la validación de eventos con datos válidos"""
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate("Título válido", "Descripción válida", scheduled_at, "AVAILABLE")
        self.assertEqual(errors, {})

    def test_event_validate_with_empty_title(self):
        """Test que verifica la validación de eventos con título vacío"""
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate("", "Descripción válida", scheduled_at, "AVAILABLE")
        self.assertIn("title", errors)
        self.assertEqual(errors["title"], "Por favor ingrese un titulo")

    def test_event_validate_with_empty_description(self):
        """Test que verifica la validación de eventos con descripción vacía"""
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate("Título válido", "", scheduled_at, "AVAILABLE")
        self.assertIn("description", errors)
        self.assertEqual(errors["description"], "Por favor ingrese una descripcion")

    def test_event_new_with_valid_data(self):
        """Test que verifica la creación de eventos con datos válidos"""
        scheduled_at = timezone.now() + datetime.timedelta(days=2)
        success, errors = Event.new(
            title="Nuevo evento",
            description="Descripción del nuevo evento",
            scheduled_at=scheduled_at,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category,
            state="AVAILABLE",
            category=self.category,
            venue=self.venue
        )

        self.assertTrue(success)
        self.assertIsNone(errors)

        # Verificar que el evento fue creado en la base de datos
        new_event = Event.objects.get(title="Nuevo evento")
        self.assertEqual(new_event.description, "Descripción del nuevo evento")
        self.assertEqual(new_event.organizer, self.organizer)
        self.assertEqual(new_event.venue, self.venue)
        self.assertEqual(new_event.category, self.category)
        self.assertEqual(new_event.state, "AVAILABLE")

    def test_event_new_with_invalid_data(self):
        """Test que verifica que no se crean eventos con datos inválidos"""
        scheduled_at = timezone.now() + datetime.timedelta(days=2)
        initial_count = Event.objects.count()

        # Intentar crear evento con título vacío
        success, errors = Event.new(
            title="",
            description="Descripción del evento",
            scheduled_at=scheduled_at,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category,
            state="AVAILABLE",
            category=self.category,
            venue=self.venue
        )

        self.assertFalse(success)
        self.assertIn("title", errors)

        # Verificar que no se creó ningún evento nuevo
        self.assertEqual(Event.objects.count(), initial_count)

    def test_event_update(self):
        """Test que verifica la actualización de eventos"""
        new_title = "Título actualizado"
        new_description = "Descripción actualizada"
        new_scheduled_at = timezone.now() + datetime.timedelta(days=3)

        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            category=self.category,
            state="AVAILABLE",
            category=self.category,
            venue=self.venue
        )

        event.update(
            title=new_title,
            description=new_description,
            scheduled_at=new_scheduled_at,
            organizer=self.organizer,
            category=self.category,
            venue=self.venue
        )

        # Recargar el evento desde la base de datos
        updated_event = Event.objects.get(pk=event.pk)

        self.assertEqual(updated_event.title, new_title)
        self.assertEqual(updated_event.description, new_description)
        self.assertEqual(updated_event.scheduled_at.time(), new_scheduled_at.time())

    def test_event_update_partial(self):
        """Test que verifica la actualización parcial de eventos"""
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            category=self.category,
            state="AVAILABLE",
            category=self.category,
            venue=self.venue
        )

        original_title = event.title
        original_scheduled_at = event.scheduled_at
        new_description = "Solo la descripción ha cambiado"

        event.update(
            title=None,  # No cambiar
            description=new_description,
            scheduled_at=None,  # No cambiar
            organizer=None, # No cambiar
            category=None,  # No cambiar
            venue=None  # No cambiar
        )

        # Recargar el evento desde la base de datos
        updated_event = Event.objects.get(pk=event.pk)

        # Verificar que solo cambió la descripción
        self.assertEqual(updated_event.title, original_title)
        self.assertEqual(updated_event.description, new_description)
        self.assertEqual(updated_event.scheduled_at, original_scheduled_at)

    def test_get_cuenta_regresiva_future_events(self):
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=2, hours= 3, minutes=15),
            organizer=self.organizer,
            category=self.category,
            venue=self.venue
        )
        cuenta_regresiva = event.get_cuenta_regresiva()
        self.assertIn("2 dias", cuenta_regresiva) 
        self.assertIn("3 horas", cuenta_regresiva) 

    def test_get_cuenta_regresiva_past_events(self):
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() - datetime.timedelta(days=1),
            organizer=self.organizer,
            category=self.category,
            venue=self.venue
        )
        self.assertIsNone(event.get_cuenta_regresiva())

    def test_get_cuenta_regresiva_menos_una_hora(self):
        now = timezone.now()
        with patch('django.utils.timezone.now', return_value=now):
            event = Event.objects.create(
                title="Evento de prueba",
                description="Descripción del evento de prueba",
                scheduled_at=now + datetime.timedelta(minutes=45),
                organizer=self.organizer,
                category=self.category,
                venue=self.venue
            )
            cuenta_regresiva=event.get_cuenta_regresiva()
            self.assertIn("0 dias", cuenta_regresiva)
            self.assertIn("0 horas", cuenta_regresiva)
            self.assertIn("45 minutos", cuenta_regresiva)