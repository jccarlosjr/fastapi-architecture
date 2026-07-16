from app.core.generics.service import GenericService
from app.modules.permissions.models import Permission
from app.modules.permissions.schemas import PermissionCreate, PermissionUpdate
from app.modules.permissions.repositories import PermissionRepository


class PermissionService(GenericService[Permission, PermissionCreate, PermissionUpdate]):
    def __init__(self, repository: PermissionRepository):
        super().__init__(repository)
        self.permission_repository = repository
