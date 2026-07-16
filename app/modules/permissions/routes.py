from app.core.generics.views import GenericAPIView
from app.modules.permissions.schemas import PermissionCreate, PermissionUpdate, PermissionRead
from app.modules.permissions.services import PermissionService
from app.modules.permissions.repositories import PermissionRepository


class PermissionAPIView(GenericAPIView[PermissionCreate, PermissionUpdate, PermissionRead]):
    prefix = ""
    tags = ["Permissions"]
    read_schema = PermissionRead
    create_schema = PermissionCreate
    update_schema = PermissionUpdate
    service_class = PermissionService
    repository_class = PermissionRepository


router = PermissionAPIView().get_router()
