from django.test import TestCase, Client
from django.urls import reverse
from app.models import User, Event, Venue, Category, Ticket
from django.utils import timezone
from datetime import timedelta

class TicketEditLimitTest(TestCase):

    def setUp(self):
        self.client = Client()
        # Creamos un usuario que va a comprar tickets
        self.user = User.objects.create_user(username="edituser", password="pass")
        self.client.login(username="edituser", password="pass")

        # Otro usuario que será el organizador del evento
        self.organizer = User.objects.create_user(username="organizer", password="pass")

        # Creamos el lugar del evento
        self.venue = Venue.objects.create(
            name="Teatro",
            city="Ciudad Ejemplo",
            address="Calle Falsa 123",
            capacity=100,
            contact="contacto@teatro.com"
        )

        # Categoría del evento
        self.category = Category.objects.create(
            name="Música",
            description="Eventos musicales",
            is_active=True
        )

        # Creamos el evento con estado "AVAILABLE" para poder comprar entradas
        self.event = Event.objects.create(
            title="Edit Ticket Event",
            description="Test evento edición ticket",
            scheduled_at=timezone.now() + timedelta(days=10),
            organizer=self.organizer,
            category=self.category,
            venue=self.venue,
            general_capacity=10,
            vip_capacity=5,
            state="AVAILABLE"
        )

    def test_edit_ticket_quantity_exceed_limit(self):
        # Creamos dos tickets distintos para este usuario en el mismo evento
        ticket1 = Ticket.objects.create(
            quantity=2,
            type="GENERAL",
            user=self.user,
            event=self.event
        )
        Ticket.objects.create(
            quantity=1,
            type="GENERAL",
            user=self.user,
            event=self.event
        )

        # Editamos el primer ticket para aumentar la cantidad
        url_edit = reverse("ticket_edit", kwargs={"id": ticket1.id})

        # Probamos con una cantidad que sumada a los otros tickets sea 4 (OK)
        response = self.client.post(url_edit, {
            "quantity": 3,  # 3 + 1 = 4 tickets, límite permitido
            "type": "GENERAL",
            "event_id": self.event.id,
        })

        # Debería redirigir porque está dentro del límite
        self.assertEqual(response.status_code, 302)
        ticket1.refresh_from_db()
        self.assertEqual(ticket1.quantity, 3)  # Para ver si se actualizó bien

        # Editamos para que la cantidad sea 4 (3+1 otro ticket = 5, supera límite)
        response = self.client.post(url_edit, {
            "quantity": 4, 
            "type": "GENERAL",
            "event_id": self.event.id,
        })

        # Ahora esperamos que NO redirija y muestre el formulario con error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No podés comprar más de 4 entradas para este evento")

        # Verificamos que la cantidad del ticket no haya cambiado (sigue 3)
        ticket1.refresh_from_db()
        self.assertEqual(ticket1.quantity, 3)
