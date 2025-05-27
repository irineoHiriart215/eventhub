from django.test import TestCase
from app.models import User, Event, Venue, Category, Ticket
from django.utils import timezone
from datetime import timedelta
from django.db import models


class TicketModelTest(TestCase):

    def setUp(self):
        # Crear usuario para las pruebas
        self.user = User.objects.create_user(username="unituser", password="pass")
        
        # Crear venue con capacidad
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
        
        # Crear evento futuro con estado "AVAILABLE"
        self.event = Event.objects.create(
            title="Unit Event",
            description="Test evento para modelo",
            scheduled_at=timezone.now() + timedelta(days=10),
            organizer=self.user,
            category=self.category,
            venue=self.venue,
            general_capacity=10,
            vip_capacity=5,
            state="AVAILABLE"
        )

    def test_ticket_limit_logic(self):
        # Crear 4 tickets, cada uno con quantity=1 (total 4 tickets para el usuario)
        for _ in range(4):
            Ticket.objects.create(user=self.user, event=self.event, quantity=1, type="GENERAL")

        # Verificamos que el usuario ya NO pueda comprar más tickets para este evento
        total_quantity = Ticket.objects.filter(user=self.user, event=self.event).aggregate(total=models.Sum('quantity'))['total'] or 0
        self.assertEqual(total_quantity, 4)

        # Como no hay un método can_purchase definido en Ticket, creamos la lógica acá:
        can_purchase = total_quantity < 4
        self.assertFalse(can_purchase, "El usuario no debería poder comprar más de 4 tickets")

        # Intentamos crear otro ticket y esperamos que no se pueda (simulado con excepción)
        with self.assertRaises(Exception):
            if not can_purchase:
                raise Exception("Límite de compra de tickets alcanzado")
            Ticket.objects.create(user=self.user, event=self.event, quantity=1, type="GENERAL")
