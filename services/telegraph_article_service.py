from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from models import TelegraphArticle
from utils.logger import logger


class TelegraphArticleService:
    """Service for Telegraph article management"""
    
    @staticmethod
    async def create_article(
        session: AsyncSession,
        title_ru: str,
        title_uz: str,
        content_html: str,
        telegraph_url: str = None,
        author_name: str = "Admin",
        tags: str = None
    ) -> TelegraphArticle:
        """Create new Telegraph article"""
        article = TelegraphArticle(
            title_ru=title_ru,
            title_uz=title_uz,
            content_html=content_html,
            telegraph_url=telegraph_url,
            author_name=author_name,
            tags=tags
        )
        session.add(article)
        await session.commit()
        await session.refresh(article)
        logger.info(f"Telegraph article created: {title_ru}")
        return article
    
    @staticmethod
    async def get_article(session: AsyncSession, article_id: int) -> Optional[TelegraphArticle]:
        """Get article by ID"""
        result = await session.execute(
            select(TelegraphArticle).where(TelegraphArticle.id == article_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_articles(session: AsyncSession) -> List[TelegraphArticle]:
        """Get all articles"""
        query = select(TelegraphArticle).order_by(TelegraphArticle.created_at.desc())
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_article(
        session: AsyncSession,
        article_id: int,
        title_ru: str = None,
        title_uz: str = None,
        content_html: str = None,
        telegraph_url: str = None,
        author_name: str = None,
        tags: str = None
    ) -> Optional[TelegraphArticle]:
        """Update Telegraph article"""
        article = await TelegraphArticleService.get_article(session, article_id)
        if not article:
            return None
        
        if title_ru is not None:
            article.title_ru = title_ru
        if title_uz is not None:
            article.title_uz = title_uz
        if content_html is not None:
            article.content_html = content_html
        if telegraph_url is not None:
            article.telegraph_url = telegraph_url
        if author_name is not None:
            article.author_name = author_name
        if tags is not None:
            article.tags = tags
        
        await session.commit()
        await session.refresh(article)
        logger.info(f"Telegraph article updated: {article_id}")
        return article
    
    @staticmethod
    async def delete_article(session: AsyncSession, article_id: int) -> bool:
        """Delete Telegraph article"""
        article = await TelegraphArticleService.get_article(session, article_id)
        if not article:
            return False
        
        await session.delete(article)
        await session.commit()
        logger.info(f"Telegraph article deleted: {article_id}")
        return True
