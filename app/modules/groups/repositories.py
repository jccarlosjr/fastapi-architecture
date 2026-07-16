from app.core.generics.repository import GenericRepository
from app.modules.groups.models import Group


class GroupRepository(GenericRepository[Group]):
    model = Group
