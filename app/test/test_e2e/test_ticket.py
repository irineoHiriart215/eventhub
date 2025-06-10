import re
from datetime import datetime, timedelta
from django.utils import timezone
from playwright.sync_api import expect
from django.urls import reverse

from app.models import User, Venue, Category, Event
from app.test.test_e2e.base import BaseE2ETest

class TicketValidation(BaseE2ETest):

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
    
    def test_ticket_validation(self):
        self.login_user("usuario", "password123")

        # Ir al formulario de compra correctamente
        ticket_url = reverse("ticket_form", args=[self.event1.id])
        self.page.goto(f"{self.live_server_url}{ticket_url}")
        
        # Esperar el input
        expect(self.page.locator("#quantity")).to_be_visible(timeout=10000)

        # Llenar y enviar
        self.page.get_by_label("Cantidad de entradas").fill("5")
        self.page.select_option("select[name='type']", label="Entrada General")
        self.page.get_by_label("Número de tarjeta").fill("1111 1111 1111 1111")
        self.page.get_by_label("Fecha de expiración").fill("11/11")
        self.page.get_by_label("CVV").fill("111")
        self.page.get_by_label("Nombre en la tarjeta").fill("Emanuel Leiva")
        self.page.get_by_label("Acepto los términos y condiciones").check()

        self.page.get_by_role("button", name="Confirmar compra").click()

        # Verificar mensaje de error
        expect(self.page.get_by_text(
            re.compile(r"No podés comprar más de 4 entradas para este evento.*")
        )).to_be_visible()
