from app.core.generics.service import GenericService
from app.modules.groups.models import Group
from app.modules.groups.schemas import GroupCreate, GroupUpdate
from app.modules.groups.repositories import GroupRepository


class GroupService(GenericService[Group, GroupCreate, GroupUpdate]):
    def __init__(self, repository: GroupRepository):
        super().__init__(repository)
        self.group_repository = repository
