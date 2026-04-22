from django.test import TestCase
from rest_framework.test import APIClient

from auth_tenants.models import Tenant, User
from chat.models import ChatMember, ChatRoom


class Phase1ApiSmokeTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Acme", slug="acme")
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="Password123!",
            name="Admin",
            role="tenant_admin",
            tenant=self.tenant,
            is_active=True,
        )
        self.staff = User.objects.create_user(
            email="staff@example.com",
            password="Password123!",
            name="Staff",
            role="staff",
            tenant=self.tenant,
            is_active=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_workspace_context_endpoint(self):
        res = self.client.get("/api/auth/workspace/context/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["tenant"]["name"], "Acme")

    def test_chat_direct_start_endpoint(self):
        res = self.client.post("/api/chat/rooms/direct/", {"user_id": self.staff.id}, format="json")
        self.assertIn(res.status_code, [200, 201])
        room = ChatRoom.objects.get(pk=res.data["data"]["id"])
        self.assertEqual(room.kind, ChatRoom.Kind.DIRECT)
        self.assertTrue(ChatMember.objects.filter(room=room, user=self.admin).exists())
        self.assertTrue(ChatMember.objects.filter(room=room, user=self.staff).exists())
