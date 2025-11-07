import re
from typing import Optional, Dict, Any, Tuple
from utils.logger import logger


class GeolocationService:
    """Service for handling geolocation and maps operations"""
    
    @staticmethod
    def parse_google_maps_url(url: str) -> Optional[Dict[str, Any]]:
        """Parse Google Maps URL to extract coordinates"""
        try:
            # Pattern 1: https://maps.google.com/?q=lat,lon
            if "?q=" in url:
                query_part = url.split("?q=")[1].split("&")[0]
                if "," in query_part:
                    lat_str, lon_str = query_part.split(",", 1)
                    lat = float(lat_str)
                    lon = float(lon_str)
                    return {
                        "latitude": lat,
                        "longitude": lon,
                        "type": "COORDINATES"
                    }
            
            # Pattern 2: https://www.google.com/maps/place/.../@lat,lon,zoom
            if "/@" in url:
                coords_part = url.split("/@")[1].split(",")[0:2]
                if len(coords_part) == 2:
                    lat = float(coords_part[0])
                    lon = float(coords_part[1])
                    return {
                        "latitude": lat,
                        "longitude": lon,
                        "type": "COORDINATES"
                    }
            
            # Pattern 3: https://maps.google.com/maps/search/...
            # For search URLs, we can't extract exact coordinates without API
            return {
                "url": url,
                "type": "SEARCH_URL"
            }
            
        except Exception as e:
            logger.error(f"Failed to parse Google Maps URL {url}: {e}")
            return None
    
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> Dict[str, Any]:
        """Validate latitude and longitude"""
        errors = []
        
        if not (-90 <= latitude <= 90):
            errors.append("Latitude must be between -90 and 90")
        
        if not (-180 <= longitude <= 180):
            errors.append("Longitude must be between -180 and 180")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def format_location_for_display(
        location_type: str,
        address_text: str = None,
        latitude: float = None,
        longitude: float = None,
        geo_name: str = None,
        maps_url: str = None
    ) -> str:
        """Format location for display in messages"""
        if location_type == "ADDRESS" and address_text:
            return f"📍 Адрес: {address_text}"
        
        elif location_type == "GEO" and latitude and longitude:
            display_name = geo_name or f"широта: {latitude:.6f}, долгота: {longitude:.6f}"
            return f"📍 Местоположение: {display_name}"
        
        elif location_type == "MAPS" and maps_url:
            return f"📍 Карта: {maps_url}"
        
        else:
            return "📍 Местоположение не указано"
    
    @staticmethod
    def format_location_for_courier(
        location_type: str,
        address_text: str = None,
        latitude: float = None,
        longitude: float = None,
        geo_name: str = None,
        maps_url: str = None
    ) -> str:
        """Format location for courier (detailed)"""
        if location_type == "ADDRESS" and address_text:
            return f"🚚 Адрес доставки:\n{address_text}"
        
        elif location_type == "GEO" and latitude and longitude:
            parts = []
            if geo_name:
                parts.append(f"🚚 Место: {geo_name}")
            parts.append(f"📍 Координаты: {latitude:.6f}, {longitude:.6f}")
            if maps_url:
                parts.append(f"🗺️ Карта: {maps_url}")
            return "\n".join(parts)
        
        elif location_type == "MAPS" and maps_url:
            return f"🚚 Адрес на карте:\n{maps_url}"
        
        else:
            return "🚚 Адрес не указан"
    
    @staticmethod
    def extract_coordinates_from_text(text: str) -> Optional[Tuple[float, float]]:
        """Extract coordinates from text message"""
        # Look for patterns like "41.2995, 69.2401" or "41.2995,69.2401"
        coord_pattern = r'(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)'
        match = re.search(coord_pattern, text)
        
        if match:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                
                # Validate coordinates
                validation = GeolocationService.validate_coordinates(lat, lon)
                if validation["is_valid"]:
                    return (lat, lon)
            except ValueError:
                pass
        
        return None
    
    @staticmethod
    def generate_google_maps_url(latitude: float, longitude: float, name: str = None) -> str:
        """Generate Google Maps URL from coordinates"""
        base_url = "https://www.google.com/maps"
        
        if name:
            # Search query with name and coordinates
            return f"{base_url}/search/?api=1&query={latitude},{longitude}"
        else:
            # Direct coordinates
            return f"{base_url}/?q={latitude},{longitude}"
    
    @staticmethod
    def calculate_distance(
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points in kilometers (Haversine formula)"""
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
              math.cos(lat1_rad) * math.cos(lat2_rad) * 
              math.sin(dlon/2)**2)
        
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        return c * r
    
    @staticmethod
    def find_nearest_couriers(
        couriers: list,
        target_lat: float,
        target_lon: float,
        max_distance_km: float = 10.0
    ) -> list:
        """Find couriers within maximum distance (if they have last known location)"""
        nearby_couriers = []
        
        for courier in couriers:
            # This would require courier location tracking
            # For now, return all couriers as we don't track their locations
            nearby_couriers.append({
                "courier": courier,
                "distance": None  # Unknown
            })
        
        return nearby_couriers
    
    @staticmethod
    def get_location_type_from_message(message_type: str) -> str:
        """Get location type from message type"""
        if message_type == "location":
            return "GEO"
        elif message_type == "text":
            # Check if text contains coordinates
            return "GEO" if GeolocationService.extract_coordinates_from_text(message_type) else "ADDRESS"
        else:
            return "ADDRESS"
    
    @staticmethod
    def clean_address_text(address: str) -> str:
        """Clean and normalize address text"""
        if not address:
            return ""
        
        # Remove extra whitespace
        address = re.sub(r'\s+', ' ', address.strip())
        
        # Basic validation
        if len(address) < 5:
            return ""
        
        return address