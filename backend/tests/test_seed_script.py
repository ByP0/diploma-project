from __future__ import annotations

from types import SimpleNamespace
import unittest

from scripts import seed


class FakePasswordService:
    def __init__(self) -> None:
        self.passwords: list[str] = []

    def hash(self, password: str) -> str:
        self.passwords.append(password)
        return f"hashed:{password}"


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def scalar(self, statement):
        return None

    async def get(self, model, entity_id):
        return None

    def add(self, item: object) -> None:
        self.added.append(item)

    async def commit(self) -> None:
        self.committed = True


class SeedScriptTests(unittest.IsolatedAsyncioTestCase):
    async def test_seed_admin_uses_current_password_hash_api(self) -> None:
        fake_session = FakeSession()
        fake_password_service = FakePasswordService()
        original_db_postgres = seed.db_postgres
        original_password_service = seed.password_service

        try:
            seed.db_postgres = SimpleNamespace(session_factory=lambda: fake_session)
            seed.password_service = fake_password_service

            await seed.seed_admin()
        finally:
            seed.db_postgres = original_db_postgres
            seed.password_service = original_password_service

        users = [item for item in fake_session.added if isinstance(item, seed.User)]
        self.assertEqual(fake_password_service.passwords, ["admin12345"])
        self.assertEqual(users[0].hashed_password, "hashed:admin12345")
        self.assertTrue(fake_session.committed)


if __name__ == "__main__":
    unittest.main()
