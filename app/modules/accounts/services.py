from app.core.generics.service import GenericService
from app.core.security import hash_password
from app.core.exceptions import DomainException
from app.modules.accounts.models import User
from app.modules.accounts.schemas import UserCreate, UserUpdate, UserPublicCreate
from app.modules.accounts.repositories import UserRepository


class UserService(GenericService[User, UserCreate, UserUpdate]):
    def __init__(self, repository: UserRepository):
        super().__init__(repository)
        self.user_repository = repository

    async def register_user(
        self, user_in: UserCreate | UserPublicCreate
    ) -> User:
        """
        Register a new user in the system.
        Verify if the e-mail is already registered.
        Hash the password.
        Create the user.
        """
        existing_user = await self.user_repository.get_by_email(user_in.email)
        if existing_user:
            raise DomainException("User with this email already exists")

        hashed_password = hash_password(user_in.password)
        new_user = await self.user_repository.create_user(user_in, hashed_password)
        return new_user
