from app.core.generics.views import GenericAPIView
from app.modules.groups.schemas import GroupCreate, GroupUpdate, GroupRead
from app.modules.groups.services import GroupService
from app.modules.groups.repositories import GroupRepository


class GroupAPIView(GenericAPIView[GroupCreate, GroupUpdate, GroupRead]):
    prefix = ""
    tags = ["Groups"]
    read_schema = GroupRead
    create_schema = GroupCreate
    update_schema = GroupUpdate
    service_class = GroupService
    repository_class = GroupRepository


router = GroupAPIView().get_router()
