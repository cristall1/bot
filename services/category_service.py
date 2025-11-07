from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from models import Category, CategoryContent, InlineButton
from utils.logger import logger


class CategoryService:
    """Service for category management"""
    
    @staticmethod
    async def create_category(
        session: AsyncSession,
        name_ru: str,
        name_uz: str,
        description_ru: str = None,
        description_uz: str = None,
        parent_id: int = None,
        level: int = 1,
        icon: str = "📁",
        category_type: str = "GENERAL",
        citizenship_scope: str = None,
        created_by_admin_id: int = None
    ) -> Category:
        """Create new category"""
        category = Category(
            name_ru=name_ru,
            name_uz=name_uz,
            description_ru=description_ru,
            description_uz=description_uz,
            parent_id=parent_id,
            level=level,
            icon=icon,
            category_type=category_type,
            citizenship_scope=citizenship_scope,
            created_by_admin_id=created_by_admin_id
        )
        session.add(category)
        await session.commit()
        await session.refresh(category)
        logger.info(f"Category created: {name_ru} (ID: {category.id})")
        return category
    
    @staticmethod
    async def get_category(session: AsyncSession, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        result = await session.execute(
            select(Category).where(and_(
                Category.id == category_id,
                Category.deleted_at.is_(None)
            ))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_categories(
        session: AsyncSession,
        active_only: bool = True,
        citizenship: str = None
    ) -> List[Category]:
        """Get all categories"""
        query = select(Category).where(Category.deleted_at.is_(None))
        
        if active_only:
            query = query.where(Category.is_active == True)
        
        if citizenship:
            query = query.where(or_(
                Category.citizenship_scope.is_(None),
                Category.citizenship_scope == citizenship
            ))
        
        query = query.order_by(Category.order_index, Category.id)
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_root_categories(
        session: AsyncSession,
        active_only: bool = True,
        citizenship: str = None
    ) -> List[Category]:
        """Get root categories (no parent)"""
        query = select(Category).where(and_(
            Category.parent_id.is_(None),
            Category.deleted_at.is_(None)
        ))
        
        if active_only:
            query = query.where(Category.is_active == True)
        
        if citizenship:
            query = query.where(or_(
                Category.citizenship_scope.is_(None),
                Category.citizenship_scope == citizenship
            ))
        
        query = query.order_by(Category.order_index, Category.id)
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_subcategories(
        session: AsyncSession,
        parent_id: int,
        active_only: bool = True,
        citizenship: str = None
    ) -> List[Category]:
        """Get subcategories of a parent"""
        query = select(Category).where(and_(
            Category.parent_id == parent_id,
            Category.deleted_at.is_(None)
        ))
        
        if active_only:
            query = query.where(Category.is_active == True)
        
        if citizenship:
            query = query.where(or_(
                Category.citizenship_scope.is_(None),
                Category.citizenship_scope == citizenship
            ))
        
        query = query.order_by(Category.order_index, Category.id)
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_category(
        session: AsyncSession,
        category_id: int,
        **kwargs
    ) -> Optional[Category]:
        """Update category"""
        category = await CategoryService.get_category(session, category_id)
        if not category:
            return None
        
        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)
        
        await session.commit()
        await session.refresh(category)
        logger.info(f"Category updated: {category.name_ru} (ID: {category_id})")
        return category
    
    @staticmethod
    async def delete_category(
        session: AsyncSession,
        category_id: int,
        soft: bool = True
    ) -> bool:
        """Delete category (soft or hard)"""
        category = await CategoryService.get_category(session, category_id)
        if not category:
            return False
        
        if soft:
            from datetime import datetime
            category.deleted_at = datetime.utcnow()
            await session.commit()
            logger.info(f"Category soft deleted: {category.name_ru} (ID: {category_id})")
        else:
            await session.delete(category)
            await session.commit()
            logger.info(f"Category hard deleted: ID {category_id}")
        
        return True
    
    @staticmethod
    async def toggle_category(session: AsyncSession, category_id: int) -> Optional[Category]:
        """Toggle category active status"""
        category = await CategoryService.get_category(session, category_id)
        if not category:
            return None
        
        category.is_active = not category.is_active
        await session.commit()
        await session.refresh(category)
        logger.info(f"Category toggled: {category.name_ru} (ID: {category_id}, Active: {category.is_active})")
        return category
    
    @staticmethod
    async def get_category_content(
        session: AsyncSession,
        category_id: int
    ) -> List[CategoryContent]:
        """Get all content for a category"""
        result = await session.execute(
            select(CategoryContent)
            .where(CategoryContent.category_id == category_id)
            .order_by(CategoryContent.created_at)
        )
        return result.scalars().all()
    
    @staticmethod
    async def add_content(
        session: AsyncSession,
        category_id: int,
        content_ru: str = None,
        content_uz: str = None,
        content_type: str = "TEXT",
        **kwargs
    ) -> CategoryContent:
        """Add content to category"""
        content = CategoryContent(
            category_id=category_id,
            content_ru=content_ru,
            content_uz=content_uz,
            content_type=content_type,
            **kwargs
        )
        session.add(content)
        await session.commit()
        await session.refresh(content)
        logger.info(f"Content added to category {category_id}")
        return content
    
    @staticmethod
    async def get_category_tree(
        session: AsyncSession,
        citizenship: str = None
    ) -> Dict:
        """Get full category tree structure"""
        root_categories = await CategoryService.get_root_categories(
            session,
            active_only=False,
            citizenship=citizenship
        )
        
        async def build_tree(category: Category) -> Dict:
            children = await CategoryService.get_subcategories(
                session,
                category.id,
                active_only=False,
                citizenship=citizenship
            )
            
            return {
                "id": category.id,
                "name_ru": category.name_ru,
                "name_uz": category.name_uz,
                "icon": category.icon,
                "level": category.level,
                "is_active": category.is_active,
                "children": [await build_tree(child) for child in children]
            }
        
        tree = []
        for root in root_categories:
            tree.append(await build_tree(root))
        
        return {"tree": tree}
