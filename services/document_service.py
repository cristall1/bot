from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from models import Document, DocumentButton
from utils.logger import logger


class DocumentService:
    """Service for document management"""
    
    @staticmethod
    async def create_document(
        session: AsyncSession,
        citizenship_scope: str,
        name_ru: str,
        name_uz: str,
        content_ru: str = None,
        content_uz: str = None,
        content_type: str = "TEXT",
        photo_file_id: str = None,
        pdf_file_id: str = None,
        audio_file_id: str = None,
        telegraph_url: str = None,
        order_index: int = 0
    ) -> Document:
        """Create new document"""
        document = Document(
            citizenship_scope=citizenship_scope,
            name_ru=name_ru,
            name_uz=name_uz,
            content_ru=content_ru,
            content_uz=content_uz,
            content_type=content_type,
            photo_file_id=photo_file_id,
            pdf_file_id=pdf_file_id,
            audio_file_id=audio_file_id,
            telegraph_url=telegraph_url,
            order_index=order_index
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)
        logger.info(f"Document created: {name_ru} for {citizenship_scope}")
        return document
    
    @staticmethod
    async def get_document(session: AsyncSession, document_id: int) -> Optional[Document]:
        """Get document by ID"""
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_documents_by_citizenship(
        session: AsyncSession,
        citizenship_scope: str,
        active_only: bool = True
    ) -> List[Document]:
        """Get all documents for specific citizenship (always fresh query)"""
        query = select(Document).where(Document.citizenship_scope == citizenship_scope)
        
        if active_only:
            query = query.where(Document.is_active == True, Document.deleted_at.is_(None))
        
        query = query.order_by(Document.order_index)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_all_documents(session: AsyncSession, active_only: bool = True) -> List[Document]:
        """Get all documents"""
        query = select(Document)
        
        if active_only:
            query = query.where(Document.is_active == True)
        
        query = query.order_by(Document.citizenship_scope, Document.order_index)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_document(
        session: AsyncSession,
        document_id: int,
        name_ru: str = None,
        name_uz: str = None,
        content_ru: str = None,
        content_uz: str = None,
        content_type: str = None,
        photo_file_id: str = None,
        pdf_file_id: str = None,
        audio_file_id: str = None,
        telegraph_url: str = None,
        order_index: int = None
    ) -> Optional[Document]:
        """Update document"""
        document = await DocumentService.get_document(session, document_id)
        if not document:
            return None
        
        if name_ru is not None:
            document.name_ru = name_ru
        if name_uz is not None:
            document.name_uz = name_uz
        if content_ru is not None:
            document.content_ru = content_ru
        if content_uz is not None:
            document.content_uz = content_uz
        if content_type is not None:
            document.content_type = content_type
        if photo_file_id is not None:
            document.photo_file_id = photo_file_id
        if pdf_file_id is not None:
            document.pdf_file_id = pdf_file_id
        if audio_file_id is not None:
            document.audio_file_id = audio_file_id
        if telegraph_url is not None:
            document.telegraph_url = telegraph_url
        if order_index is not None:
            document.order_index = order_index
        
        await session.commit()
        await session.refresh(document)
        logger.info(f"Document updated: {document_id}")
        return document
    
    @staticmethod
    async def delete_document(session: AsyncSession, document_id: int) -> bool:
        """Delete document (soft delete)"""
        document = await DocumentService.get_document(session, document_id)
        if not document:
            return False
        
        from datetime import datetime
        document.deleted_at = datetime.utcnow()
        document.is_active = False
        await session.commit()
        logger.info(f"Document deleted: {document_id}")
        return True
    
    @staticmethod
    async def add_button(
        session: AsyncSession,
        document_id: int,
        text_ru: str,
        text_uz: str,
        button_type: str = "LINK",
        button_value: str = None,
        button_interface: dict = None,
        order_index: int = 0
    ) -> Optional[DocumentButton]:
        """Add button to document"""
        document = await DocumentService.get_document(session, document_id)
        if not document:
            return None
        
        button = DocumentButton(
            document_id=document_id,
            text_ru=text_ru,
            text_uz=text_uz,
            button_type=button_type,
            button_value=button_value or "",
            button_interface=button_interface,
            order_index=order_index
        )
        session.add(button)
        await session.commit()
        await session.refresh(button)
        logger.info(f"Button added to document {document_id}")
        return button
    
    @staticmethod
    async def get_document_buttons(session: AsyncSession, document_id: int) -> List[DocumentButton]:
        """Get all buttons for document"""
        query = select(DocumentButton).where(
            DocumentButton.document_id == document_id,
            DocumentButton.is_active == True
        ).order_by(DocumentButton.order_index)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def delete_button(session: AsyncSession, button_id: int) -> bool:
        """Delete button"""
        result = await session.execute(
            select(DocumentButton).where(DocumentButton.id == button_id)
        )
        button = result.scalar_one_or_none()
        
        if not button:
            return False
        
        await session.delete(button)
        await session.commit()
        logger.info(f"Button deleted: {button_id}")
        return True
