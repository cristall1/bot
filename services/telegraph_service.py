from telegraph import Telegraph
from config import settings
from utils.logger import logger
from typing import Optional


class TelegraphService:
    """Service for Telegraph integration"""
    
    def __init__(self):
        self.telegraph = Telegraph()
        self.token = settings.telegraph_token
        
        if not self.token:
            try:
                self.telegraph.create_account(
                    short_name="AlAzharDirassa",
                    author_name="Al-Azhar & Dirassa Bot"
                )
                self.token = self.telegraph.get_access_token()
                logger.info("Telegraph token auto-generated")
            except Exception as e:
                logger.error(f"Failed to create Telegraph account: {e}")
    
    def create_article(
        self,
        title: str,
        content: str,
        author_name: str = "Al-Azhar & Dirassa"
    ) -> Optional[str]:
        """Create Telegraph article and return URL"""
        try:
            response = self.telegraph.create_page(
                title=title,
                html_content=content,
                author_name=author_name
            )
            url = f"https://telegra.ph/{response['path']}"
            logger.info(f"Telegraph article created: {url}")
            return url
        except Exception as e:
            logger.error(f"Failed to create Telegraph article: {e}")
            return None
    
    def update_article(
        self,
        path: str,
        title: str,
        content: str
    ) -> Optional[str]:
        """Update existing Telegraph article"""
        try:
            response = self.telegraph.edit_page(
                path=path,
                title=title,
                html_content=content
            )
            url = f"https://telegra.ph/{response['path']}"
            logger.info(f"Telegraph article updated: {url}")
            return url
        except Exception as e:
            logger.error(f"Failed to update Telegraph article: {e}")
            return None
    
    @staticmethod
    def format_content(text: str) -> str:
        """Format text for Telegraph"""
        text = text.replace('\n', '<br>')
        
        return f"<p>{text}</p>"
    
    @staticmethod
    def is_long_content(text: str, threshold: int = 1000) -> bool:
        """Check if content should be moved to Telegraph"""
        return len(text) > threshold


telegraph_service = TelegraphService()
