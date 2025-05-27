import unittest
from django.contrib.auth import get_user_model
from playwright.sync_api import sync_playwright


class TicketPurchaseTest(unittest.TestCase):
    def setUp(self):
        User = get_user_model()
        User.objects.filter(username="testuser").delete()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.page = self.browser.new_page()

    def tearDown(self):
        self.browser.close()
        self.playwright.stop()
        self.user.delete()

    def test_user_can_create_ticket_with_quantity_4(self):
        # Login
        self.page.goto("http://127.0.0.1:8000/accounts/login/")
        self.page.fill('input[name="username"]', 'testuser')
        self.page.fill('input[name="password"]', 'testpass123')
        self.page.click('button[type="submit"]')

        self.page.wait_for_url("http://127.0.0.1:8000/events/")

        # Ir al form de compra
        self.page.goto("http://127.0.0.1:8000/ticket/create/1")

        self.page.select_option("#type", "GENERAL")
        self.page.fill("#card_number", "1234567812345678")
        self.page.fill("#expiry_date", "12/25")
        self.page.fill("#cvv", "123")
        self.page.fill("#card_name", "Juan Pérez")
        self.page.check("#terms")
        self.page.fill("#quantity", "4")

        # Enviar formulario
        with self.page.expect_navigation():
            self.page.click("button[type=submit]")

        print("Redirigido a:", self.page.url)

        # Verificar que no aparece mensaje de error
        page_content = self.page.content()
        self.assertNotIn("No podés comprar más de", page_content)


if __name__ == "__main__":
    unittest.main()
