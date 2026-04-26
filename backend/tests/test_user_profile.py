from datetime import datetime, timezone
from types import SimpleNamespace
import unittest
from uuid import uuid4

from pydantic import ValidationError

from app.core.security import password_service
from app.schemas.user import UserAdminUpdate, UserProfileUpdate, UserRead
from app.services.user_service import UserService


class FakeSession:
    def __init__(self) -> None:
        self.commit_calls = 0
        self.refresh_calls = 0
        self.rollback_calls = 0
        self.executed = []

    async def get(self, *_args, **_kwargs):
        return None

    async def execute(self, statement):
        self.executed.append(statement)
        return None

    async def commit(self) -> None:
        self.commit_calls += 1

    async def refresh(self, _instance) -> None:
        self.refresh_calls += 1

    async def rollback(self) -> None:
        self.rollback_calls += 1


class FakeImageService:
    def __init__(self) -> None:
        self.deleted_ids: list[str] = []
        self.next_image_id = "6622eacaf2f4b22a4eb8ac11"

    async def upload(self, _file):
        return SimpleNamespace(id=self.next_image_id)

    async def delete(self, image_id: str) -> None:
        self.deleted_ids.append(image_id)


class UserProfileSchemaTests(unittest.TestCase):
    def test_password_change_requires_current_password(self) -> None:
        with self.assertRaises(ValidationError):
            UserProfileUpdate(new_password="NewPassword1!")

    def test_user_read_builds_avatar_url(self) -> None:
        model = UserRead.model_validate(
            SimpleNamespace(
                id=uuid4(),
                email="buyer@example.com",
                name="Ivan",
                avatar_image_id="6622eacaf2f4b22a4eb8ac11",
                role="user",
                is_active=True,
                is_blocked=False,
                blocked_at=None,
                blocked_reason=None,
                email_verified_at=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )

        self.assertEqual(model.avatar_url, "/api/images/6622eacaf2f4b22a4eb8ac11")
        self.assertFalse(model.is_email_verified)

    def test_admin_update_defaults_block_reason(self) -> None:
        payload = UserAdminUpdate(is_blocked=True)
        self.assertEqual(payload.blocked_reason, "Blocked by staff")


class UserServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_update_profile_changes_name_and_password(self) -> None:
        session = FakeSession()
        user = SimpleNamespace(
            id=uuid4(),
            name="Old Name",
            hashed_password=password_service.hash("Password1!"),
        )

        updated_user = await UserService(session).update_profile(
            user,
            name="New Name",
            current_password="Password1!",
            new_password="NewPassword1!",
        )

        self.assertEqual(updated_user.name, "New Name")
        self.assertTrue(password_service.verify("NewPassword1!", updated_user.hashed_password))
        self.assertEqual(session.commit_calls, 1)
        self.assertEqual(session.refresh_calls, 1)
        self.assertEqual(len(session.executed), 1)

    async def test_upload_avatar_replaces_previous_image(self) -> None:
        session = FakeSession()
        image_service = FakeImageService()
        user = SimpleNamespace(
            id=uuid4(),
            name="Ivan",
            hashed_password=password_service.hash("Password1!"),
            avatar_image_id="6622eacaf2f4b22a4eb8ac10",
        )

        updated_user = await UserService(session, image_service=image_service).upload_avatar(
            user,
            file=object(),
        )

        self.assertEqual(updated_user.avatar_image_id, "6622eacaf2f4b22a4eb8ac11")
        self.assertEqual(session.commit_calls, 1)
        self.assertEqual(session.refresh_calls, 1)
        self.assertEqual(image_service.deleted_ids, ["6622eacaf2f4b22a4eb8ac10"])
