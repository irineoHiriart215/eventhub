from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from app.models import User, Event, Venue, Category, Ticket
from django.utils import timezone
from datetime import timedelta
from playwright.sync_api import sync_playwright
import time
from django.test.utils import override_settings

@override_settings(DJANGO_ALLOW_ASYNC_UNSAFE=True)
class TicketEditLimitE2ETest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.page = cls.browser.new_page()

    @classmethod
    def tearDownClass(cls):
        cls.page.close()
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username="edituser", password="pass")
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.venue = Venue.objects.create(
            name="Teatro", city="Ciudad", address="Calle Falsa 123",
            capacity=100, contact="teatro@ejemplo.com"
        )
        self.category = Category.objects.create(
            name="Música", description="Musicales", is_active=True
        )
        self.event = Event.objects.create(
            title="Edit Ticket Event", description="test evento",
            scheduled_at=timezone.now() + timedelta(days=10),
            organizer=self.organizer, category=self.category,
            venue=self.venue, general_capacity=10, vip_capacity=5,
            state="AVAILABLE"
        )
        self.ticket1 = Ticket.objects.create(
            quantity=2, type="GENERAL", user=self.user, event=self.event
        )
        self.ticket2 = Ticket.objects.create(
            quantity=1, type="GENERAL", user=self.user, event=self.event
        )

    def login_and_edit_ticket(self, new_quantity):
        # Login
        self.page.goto(f"{self.live_server_url}/accounts/login/")
        self.page.fill('input[name="username"]', "edituser")
        self.page.fill('input[name="password"]', "pass")
        self.page.click('button[type="submit"]')
        self.page.wait_for_url(f"{self.live_server_url}/")  

        # Ir al formulario de edición del ticket
        edit_url = f"{self.live_server_url}{reverse('ticket_edit', kwargs={'id': self.ticket1.id})}"
        self.page.goto(edit_url)

        # Cambiar la cantidad
        self.page.fill('input[name="quantity"]', str(new_quantity))
        self.page.select_option('select[name="type"]', 'GENERAL')
        self.page.click('button[type="submit"]')
        time.sleep(1)

    def test_edit_within_limit_then_exceed_limit(self):
        # --- Paso 1: editar a 3 (total = 3 + 1 = 4 → OK)
        self.login_and_edit_ticket(new_quantity=3)
        self.ticket1.refresh_from_db()
        self.assertEqual(self.ticket1.quantity, 3)

        # --- Paso 2: intentar editar a 4 (total = 4 + 1 = 5 → ERROR)
        self.login_and_edit_ticket(new_quantity=4)
        self.ticket1.refresh_from_db()
        self.assertEqual(self.ticket1.quantity, 3)  # No cambió

        # Verificamos que el error se muestra
        self.assertIn("No podés comprar más de 4 entradas", self.page.content())
