from django.test import TestCase, Client
from django.urls import reverse
from app.models import User, Event, Venue, Category, Ticket
from django.utils import timezone
from datetime import timedelta
from django.db import models

class TicketIntegrationTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="intuser", password="pass")
        self.client.login(username="intuser", password="pass")

        self.venue = Venue.objects.create(
            name="Teatro",
            city="Ciudad Ejemplo",
            address="Calle Falsa 123",
            capacity=100,
            contact="contacto@teatro.com"
        )

        self.category = Category.objects.create(
            name="Música",
            description="Eventos musicales",
            is_active=True
        )

        self.event = Event.objects.create(
            title="Integration Event",
            description="Test",
            scheduled_at=timezone.now() + timedelta(days=10),
            organizer=self.user,
            category=self.category,
            venue=self.venue
        )

    def test_ticket_purchase_limit_integration(self):
        url = reverse("ticket_form", kwargs={"event_id": self.event.id})

        # Comprar 4 tickets en total (cantidad 1 c/u)
        for _ in range(4):
            response = self.client.post(url, {
                "quantity": 1,
                "type": "GENERAL",
                "event_id": self.event.id,
            })
            self.assertEqual(response.status_code, 302)  # Redirige al éxito

        # Intentar comprar 2 tickets más (excede límite)
        response = self.client.post(url, {
            "quantity": 2,
            "type": "GENERAL",
            "event_id": self.event.id,
        })

        self.assertEqual(response.status_code, 200)  # No redirige, vuelve al form
        self.assertContains(response, "No podés comprar más de 4 entradas para este evento")
        
        # Verificar que no se hayan creado tickets extra
        total_tickets = Ticket.objects.filter(user=self.user, event=self.event).aggregate(total=models.Sum('quantity'))['total']
        self.assertEqual(total_tickets, 4)
