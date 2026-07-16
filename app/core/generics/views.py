import inspect
from typing import Any, Callable, ClassVar, Generic, Optional, Type, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.params import Depends as DependsMarker
from pydantic import BaseModel

from app.core.generics.service import GenericService
from app.core.generics.repository import GenericRepository
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ReadSchemaType = TypeVar("ReadSchemaType", bound=BaseModel)


_ROUTE_CONFIG_ATTRS = {
    "method",
    "path",
    "response_model",
    "status_code",
    "tags",
    "summary"
}


class APIEndpoint:
    """
    Base class for a class-based FastAPI endpoint.
    It resolves class-level dependencies (annotated with Depends)
    and passes the remaining arguments to `handle`.
    """
    method: ClassVar[str] = "GET"
    path: ClassVar[str] = "/"
    response_model: ClassVar[Optional[Type]] = None
    status_code: ClassVar[int] = status.HTTP_200_OK
    tags: ClassVar[Optional[list[str]]] = None
    summary: ClassVar[Optional[str]] = None

    async def handle(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    @classmethod
    def register(cls, router: APIRouter) -> None:
        route_function = cls._build_route_function()
        router.add_api_route(
            cls.path,
            route_function,
            methods=[cls.method],
            response_model=cls.response_model,
            status_code=cls.status_code,
            tags=cls.tags,
            summary=cls.summary or (cls.handle.__doc__ or "").strip() or None,
        )

    @classmethod
    def _build_route_function(cls) -> Callable:
        dependency_params = cls._get_dependency_params()
        dependency_names = {param.name for param in dependency_params}
        handle_params = cls._get_handle_params()

        original_signature = inspect.signature(cls.handle)
        combined_signature = original_signature.replace(
            parameters=handle_params + dependency_params
        )

        async def route_function(**resolved_kwargs: Any) -> Any:
            instance = cls()
            for name in dependency_names:
                setattr(instance, name, resolved_kwargs.pop(name))
            if hasattr(instance, "check_access"):
                await instance.check_access()
            return await instance.handle(**resolved_kwargs)

        route_function.__signature__ = combined_signature
        route_function.__name__ = cls.__name__
        route_function.__doc__ = cls.handle.__doc__
        return route_function

    async def check_access(self) -> None:
        """Hook to run access checks before handle is invoked."""
        pass

    @classmethod
    def _get_dependency_params(cls) -> list[inspect.Parameter]:
        params = []
        for name, annotation in cls._collect_annotations().items():
            if name in _ROUTE_CONFIG_ATTRS or name.startswith("_"):
                continue
            value = getattr(cls, name, None)
            if not isinstance(value, DependsMarker):
                continue
            params.append(
                inspect.Parameter(
                    name,
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    default=value,
                    annotation=annotation,
                )
            )
        return params

    @classmethod
    def _collect_annotations(cls) -> dict[str, Any]:
        merged = {}
        for klass in reversed(cls.__mro__):
            merged.update(getattr(klass, "__annotations__", {}))
        return merged

    @classmethod
    def _get_handle_params(cls) -> list[inspect.Parameter]:
        signature = inspect.signature(cls.handle)
        return list(signature.parameters.values())[1:]


from app.modules.accounts.dependencies import get_current_user
from app.modules.accounts.models import User
from fastapi import HTTPException


class CreateAPIEndpoint(APIEndpoint):
    method = "POST"
    status_code = status.HTTP_201_CREATED


class RetrieveAPIEndpoint(APIEndpoint):
    method = "GET"
    status_code = status.HTTP_200_OK


class UpdateAPIEndpoint(APIEndpoint):
    method = "PATCH"
    status_code = status.HTTP_200_OK


class GenericAPIView(Generic[CreateSchemaType, UpdateSchemaType, ReadSchemaType]):
    """
    Equivalente a um ModelViewSet do DRF. Cada app define:
      - prefix / tags
      - read_schema / create_schema / update_schema
      - service_class / repository_class
      - get_service_dependency() -> callable usado em Depends()

    O NotFoundError deve ser tratado por um exception_handler global
    (ver main.py), então as rotas ficam limpas, sem try/except repetido.
    """

    prefix: str
    tags: list[str] = []
    read_schema: Type[ReadSchemaType]
    create_schema: Type[CreateSchemaType]
    update_schema: Type[UpdateSchemaType]
    service_class: Type[GenericService]
    repository_class: Type[GenericRepository]

    # Dependências extras aplicadas a TODAS as rotas (ex: auth). Sobrescreva se precisar.
    common_dependencies: list[Depends] = []

    def get_service_dependency(self) -> Callable[..., GenericService]:
        """
        Retorna a função factory do service. Por padrão, monta o service usando
        service_class e repository_class. Sobrescreva se precisar de lógica customizada.
        """
        service_cls = self.service_class
        repo_cls = self.repository_class

        async def dependency(db: AsyncSession = Depends(get_db)) -> GenericService:
            return service_cls(repo_cls(db))

        return dependency

    def get_router(self) -> APIRouter:
        router = APIRouter(
            prefix=self.prefix, tags=self.tags, dependencies=self.common_dependencies
        )
        service_dep = self.get_service_dependency()

        @router.get("/", response_model=list[self.read_schema])
        async def list_objects(
            offset: int = 0,
            limit: int = 100,
            service: GenericService = Depends(service_dep),
            current_user: User = Depends(get_current_user),
        ):
            model_name = service.repository.model.__name__.lower()
            if not current_user.has_permission(f"view_{model_name}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission view_{model_name} required",
                )
            return await service.list(offset=offset, limit=limit)

        @router.post(
            "/", response_model=self.read_schema, status_code=status.HTTP_201_CREATED
        )
        async def create_object(
            obj_in: self.create_schema,
            service: GenericService = Depends(service_dep),
            current_user: User = Depends(get_current_user),
        ):
            model_name = service.repository.model.__name__.lower()
            if not current_user.has_permission(f"add_{model_name}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission add_{model_name} required",
                )
            return await service.create(obj_in)

        @router.get("/{id}", response_model=self.read_schema)
        async def retrieve_object(
            id: UUID,
            service: GenericService = Depends(service_dep),
            current_user: User = Depends(get_current_user),
        ):
            model_name = service.repository.model.__name__.lower()
            if not current_user.has_permission(f"view_{model_name}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission view_{model_name} required",
                )
            return await service.get(id)

        @router.patch("/{id}", response_model=self.read_schema)
        async def update_object(
            id: UUID,
            obj_in: self.update_schema,
            service: GenericService = Depends(service_dep),
            current_user: User = Depends(get_current_user),
        ):
            model_name = service.repository.model.__name__.lower()
            if not current_user.has_permission(f"change_{model_name}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission change_{model_name} required",
                )
            return await service.update(id, obj_in)

        @router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
        async def delete_object(
            id: UUID,
            service: GenericService = Depends(service_dep),
            current_user: User = Depends(get_current_user),
        ):
            model_name = service.repository.model.__name__.lower()
            if not current_user.has_permission(f"delete_{model_name}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission delete_{model_name} required",
                )
            await service.delete(id)

        # Hook de extensão: subclasses podem adicionar rotas customizadas.
        self.extra_routes(router, service_dep)
        return router

    def extra_routes(self, router: APIRouter, service_dep: Callable) -> None:
        """Sobrescreva para adicionar rotas além do CRUD padrão (ex: /clientes/{id}/ativar)."""
        pass
