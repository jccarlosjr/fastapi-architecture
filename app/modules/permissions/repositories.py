from app.core.generics.repository import GenericRepository
from app.modules.permissions.models import Permission


class PermissionRepository(GenericRepository[Permission]):
    model = Permission
