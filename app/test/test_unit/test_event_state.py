import datetime
from django.utils import timezone
from django.test import TestCase
from app.models import Event, Venue, Category, User

class EventStateTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )
        
        self.venue = Venue.objects.create(
            name = "Estadio de ejemplo",
            city = "Ciudad de ejemplo",
            address = "Calle 123",
            capacity = "100",
            contact = "Contactos del estadio",
        )
        
        self.category = Category.objects.create(
            name = "Categoria 1",
            description = "Descripcion",
            is_active = True,
        )

    def test_event_state_valid(self): 
        """Test que verifica que se pueda crear un evento con cualquiera de los estados disponibles"""       
        for state, _ in Event.EVENT_STATE:
            evento = Event.objects.create(
                title="Evento de prueba",
                description="Descripción del evento de prueba",
                scheduled_at=timezone.now() + datetime.timedelta(days=1),
                organizer=self.organizer,
                venue=self.venue,
                category=self.category,
                state=state
            )
            self.assertEqual(evento.state, state)
            
    def test_event_state_default(self):
        """Test que verifica que al crear un evento si no se ingresa un estado tiene que ser 'AVAILABLE' por default"""
        event = Event.objects.create(
                title="Evento de prueba",
                description="Descripción del evento de prueba",
                scheduled_at=timezone.now() + datetime.timedelta(days=1),
                organizer=self.organizer,
                venue=self.venue,
                category=self.category,
            )
        self.assertEqual(event.state, "AVAILABLE")
        
    def test_event_state_invalid(self):
        """Test que verifica que no se puede crear un evento con estado invalido"""
        initial_count = Event.objects.count()
        
        success, errors = Event.new(
            title="Evento de prueba",
            description="Descripción del evento",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            category=self.category,
            state="FAKE_STATE",
        )

        self.assertFalse(success)
        self.assertIn("state", errors)
        
        self.assertEqual(Event.objects.count(), initial_count)
        