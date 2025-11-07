import json
import re
from typing import Dict, List, Optional
from utils.logger import logger


class ContentParser:
    """Parse result.json to extract Al-Azhar and Dirassa information"""
    
    def __init__(self, json_file: str = "result.json"):
        self.json_file = json_file
        self.data = None
    
    def load_data(self) -> bool:
        """Load JSON data"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        except Exception as e:
            logger.error(f"Error loading {self.json_file}: {e}")
            return False
    
    def extract_messages(self) -> List[Dict]:
        """Extract all messages from JSON"""
        if not self.data:
            return []
        
        messages = self.data.get("messages", [])
        return [msg for msg in messages if isinstance(msg.get("text"), str)]
    
    def find_dirassa_info(self) -> Dict:
        """Extract Dirassa-related information"""
        dirassa_info = {
            "levels": [],
            "books": [],
            "curriculum": [],
            "pricing": [],
            "general": []
        }
        
        messages = self.extract_messages()
        
        dirassa_keywords = [
            "dirassa", "дирасса", "курс", "уровень", "level",
            "A0", "A1", "A2", "B1", "B2", "C1", "C2",
            "учебник", "книга", "book", "kitob"
        ]
        
        for msg in messages:
            text = msg.get("text", "").lower()
            
            if any(keyword in text for keyword in dirassa_keywords):
                if any(level in text.upper() for level in ["A0", "A1", "A2", "B1", "B2", "C1", "C2"]):
                    dirassa_info["levels"].append(msg.get("text", ""))
                elif "книга" in text or "book" in text or "учебник" in text:
                    dirassa_info["books"].append(msg.get("text", ""))
                elif "цена" in text or "стоимость" in text or "price" in text:
                    dirassa_info["pricing"].append(msg.get("text", ""))
                elif "программа" in text or "curriculum" in text:
                    dirassa_info["curriculum"].append(msg.get("text", ""))
                else:
                    dirassa_info["general"].append(msg.get("text", ""))
        
        return dirassa_info
    
    def find_alazhar_info(self) -> Dict:
        """Extract Al-Azhar-related information"""
        alazhar_info = {
            "faculties": [],
            "requirements": [],
            "visa": [],
            "documents": [],
            "scholarships": [],
            "contacts": [],
            "general": []
        }
        
        messages = self.extract_messages()
        
        alazhar_keywords = [
            "al-azhar", "аль-азхар", "азхар", "azhar",
            "факультет", "faculty", "шариат", "sharia",
            "языки", "language", "инженерия", "engineering"
        ]
        
        for msg in messages:
            text = msg.get("text", "").lower()
            
            if any(keyword in text for keyword in alazhar_keywords):
                if "факультет" in text or "faculty" in text:
                    alazhar_info["faculties"].append(msg.get("text", ""))
                elif "требование" in text or "requirement" in text or "документ" in text:
                    alazhar_info["requirements"].append(msg.get("text", ""))
                elif "виза" in text or "visa" in text or "икама" in text or "iqama" in text:
                    alazhar_info["visa"].append(msg.get("text", ""))
                elif "стипендия" in text or "scholarship" in text or "грант" in text:
                    alazhar_info["scholarships"].append(msg.get("text", ""))
                elif "контакт" in text or "contact" in text or "телефон" in text or "phone" in text:
                    alazhar_info["contacts"].append(msg.get("text", ""))
                else:
                    alazhar_info["general"].append(msg.get("text", ""))
        
        return alazhar_info
    
    def find_contacts(self) -> List[Dict]:
        """Extract contact information"""
        contacts = []
        messages = self.extract_messages()
        
        phone_pattern = re.compile(r'[\+]?[0-9]{10,15}')
        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        
        for msg in messages:
            text = msg.get("text", "")
            
            phones = phone_pattern.findall(text)
            emails = email_pattern.findall(text)
            
            if phones or emails:
                contacts.append({
                    "text": text,
                    "phones": phones,
                    "emails": emails
                })
        
        return contacts
    
    def extract_urls(self) -> List[str]:
        """Extract all URLs from messages"""
        urls = []
        messages = self.extract_messages()
        
        url_pattern = re.compile(r'https?://[^\s]+')
        
        for msg in messages:
            text = msg.get("text", "")
            found_urls = url_pattern.findall(text)
            urls.extend(found_urls)
        
        return list(set(urls))
    
    def parse_all(self) -> Dict:
        """Parse all content"""
        if not self.load_data():
            return {}
        
        return {
            "dirassa": self.find_dirassa_info(),
            "alazhar": self.find_alazhar_info(),
            "contacts": self.find_contacts(),
            "urls": self.extract_urls(),
            "total_messages": len(self.extract_messages())
        }
    
    def export_to_json(self, output_file: str = "data/dirassa_content.json"):
        """Export parsed data to JSON"""
        parsed_data = self.parse_all()
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Parsed data exported to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False
