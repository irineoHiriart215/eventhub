from django.test import TestCase
from app.models import User, Event, Venue, Category, Ticket
from django.utils import timezone
from datetime import timedelta

class TicketModelTest(TestCase):

    def setUp(self):
        # Crear usuario
        self.user = User.objects.create_user(username="unituser", password="pass")
        
        # Crear venue (completo con capacity)
        self.venue = Venue.objects.create(
            name="Teatro",
            city="Ciudad Ejemplo",
            address="Calle Falsa 123",
            capacity=100,
            contact="contacto@teatro.com"
        )

        # Crear categoría
        self.category = Category.objects.create(
            name="Música",
            description="Eventos musicales",
            is_active=True
        )
        
        # Crear evento futuro
        self.event = Event.objects.create(
            title="Unit Event",
            description="Test",
            scheduled_at=timezone.now() + timedelta(days=10),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )

    def test_ticket_limit_logic(self):
    # Crear 4 tickets de quantity=1 (total: 4)
        for _ in range(4):
            Ticket.objects.create(user=self.user, event=self.event, quantity=1)

        # Verificar que NO puede comprar más
        can_purchase = Ticket.can_purchase(self.user, self.event)
        self.assertFalse(can_purchase, "El usuario no debería poder comprar más de 4 tickets")

        # Verificar que crear otro ticket lanza excepción (si vos después controlás eso manualmente)
        with self.assertRaises(Exception):
            if not Ticket.can_purchase(self.user, self.event):
                raise Exception("Límite alcanzado")
            Ticket.objects.create(user=self.user, event=self.event, quantity=1)

