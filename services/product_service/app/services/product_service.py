import math
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityAlreadyExistsException, EntityNotFoundException
from app.core.telemetry import get_tracer
from app.models.category import Category
from app.models.product import Product
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.common import PaginatedData, PaginationMeta, PaginationParams
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

tracer = get_tracer("product_service")


class ProductCatalogService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cat_repo = CategoryRepository(session)
        self.prod_repo = ProductRepository(session)

    # Categories
    async def create_category(self, cat_in: CategoryCreate) -> CategoryResponse:
        with tracer.start_as_current_span("catalog.create_category") as span:
            span.set_attribute("category.name", cat_in.name)
            span.set_attribute("category.slug", cat_in.slug)

            if await self.cat_repo.get_by_slug(cat_in.slug):
                raise EntityAlreadyExistsException("Category", "slug", cat_in.slug)

            new_cat = Category(
                name=cat_in.name.strip(),
                slug=cat_in.slug.strip().lower(),
                description=cat_in.description,
            )
            cat = await self.cat_repo.create(new_cat)
            await self.session.commit()
            await self.session.refresh(cat)
            span.set_attribute("category.uuid", cat.uuid)
            return CategoryResponse.model_validate(cat)

    async def list_categories(self) -> List[CategoryResponse]:
        with tracer.start_as_current_span("catalog.list_categories"):
            cats = await self.cat_repo.list_all()
            return [CategoryResponse.model_validate(c) for c in cats]

    # Products
    async def create_product(self, prod_in: ProductCreate) -> ProductResponse:
        with tracer.start_as_current_span("catalog.create_product") as span:
            span.set_attribute("product.sku", prod_in.sku)
            span.set_attribute("product.name", prod_in.name)

            cat = await self.cat_repo.get_by_uuid(prod_in.category_uuid)
            if not cat:
                raise EntityNotFoundException("Category", prod_in.category_uuid)

            if await self.prod_repo.get_by_sku(prod_in.sku):
                raise EntityAlreadyExistsException("Product", "SKU", prod_in.sku)

            if await self.prod_repo.get_by_slug(prod_in.slug):
                raise EntityAlreadyExistsException("Product", "slug", prod_in.slug)

            new_prod = Product(
                category_id=cat.id,
                name=prod_in.name.strip(),
                slug=prod_in.slug.strip().lower(),
                sku=prod_in.sku.strip().upper(),
                description=prod_in.description,
                price=prod_in.price,
                currency=prod_in.currency,
                is_active=prod_in.is_active,
            )
            prod = await self.prod_repo.create(new_prod)
            await self.session.commit()
            await self.session.refresh(prod)
            span.set_attribute("product.uuid", prod.uuid)
            return ProductResponse.model_validate(prod)

    async def get_product(self, identifier: str) -> ProductResponse:
        with tracer.start_as_current_span("catalog.get_product") as span:
            span.set_attribute("product.identifier", identifier)
            prod = await self.prod_repo.get_by_uuid(identifier)
            if not prod:
                prod = await self.prod_repo.get_by_sku(identifier)
            if not prod:
                raise EntityNotFoundException("Product", identifier)
            return ProductResponse.model_validate(prod)

    async def list_products(
        self,
        pagination: PaginationParams,
        category_uuid: Optional[str] = None,
        is_active: Optional[bool] = True,
        search_query: Optional[str] = None,
    ) -> PaginatedData[ProductResponse]:
        with tracer.start_as_current_span("catalog.list_products") as span:
            cat_id = None
            if category_uuid:
                cat = await self.cat_repo.get_by_uuid(category_uuid)
                if cat:
                    cat_id = cat.id

            items, total = await self.prod_repo.list_products(
                offset=pagination.offset,
                limit=pagination.size,
                category_id=cat_id,
                is_active=is_active,
                search_query=search_query,
            )

            total_pages = math.ceil(total / pagination.size) if total > 0 else 1
            meta = PaginationMeta(
                total_records=total,
                current_page=pagination.page,
                page_size=pagination.size,
                total_pages=total_pages,
                has_next=pagination.page < total_pages,
                has_prev=pagination.page > 1,
            )
            span.set_attribute("catalog.total_records", total)
            return PaginatedData(
                items=[ProductResponse.model_validate(p) for p in items],
                pagination=meta,
            )

