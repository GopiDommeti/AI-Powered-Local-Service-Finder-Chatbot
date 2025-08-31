import chromadb
import json
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ServiceVectorDB:
    def __init__(self, db_path: str = "./chroma_db"):
        """
        Initialize ChromaDB for service data storage and retrieval
        
        Args:
            db_path: Path to store the ChromaDB database
        """
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="services",
            metadata={"description": "Local service listings from JustDial"}
        )
        
        print(f"✅ Connected to ChromaDB at {db_path}")
    
    def add_services(self, services: List[Dict[str, Any]]) -> bool:
        """
        Add services to the vector database
        
        Args:
            services: List of service dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not services:
                print("⚠️ No services to add")
                return False
            
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for i, service in enumerate(services):
                # Create a searchable document
                doc_text = self._create_service_document(service)
                
                # Create metadata
                metadata = {
                    "name": service.get("name", ""),
                    "category": service.get("category", ""),
                    "address": service.get("address", ""),
                    "phone": service.get("phone", ""),
                    "rating": service.get("rating", ""),
                    "price": service.get("price", ""),
                    "location": self._extract_location(service.get("address", "")),
                    "price_numeric": self._extract_price_numeric(service.get("price", ""))
                }
                
                documents.append(doc_text)
                metadatas.append(metadata)
                ids.append(f"service_{i}_{hash(service.get('name', ''))}")
            
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ Added {len(services)} services to vector database")
            return True
            
        except Exception as e:
            print(f"❌ Error adding services to vector database: {str(e)}")
            return False
    
    def search_services(self, query: str, n_results: int = 5, 
                       category_filter: Optional[str] = None,
                       max_price: Optional[float] = None,
                       location_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for services using semantic similarity
        
        Args:
            query: Search query
            n_results: Number of results to return
            category_filter: Filter by category
            max_price: Maximum price filter
            location_filter: Filter by location
            
        Returns:
            List of matching services with metadata
        """
        try:
            # Perform search without filters first
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2  # Get more results to filter from
            )
            
            # Format results
            services = []
            if results['metadatas'] and results['metadatas'][0]:
                for metadata in results['metadatas'][0]:
                    service = {
                        "name": metadata.get("name", ""),
                        "category": metadata.get("category", ""),
                        "address": metadata.get("address", ""),
                        "phone": metadata.get("phone", ""),
                        "rating": metadata.get("rating", ""),
                        "price": metadata.get("price", ""),
                        "location": metadata.get("location", ""),
                        "price_numeric": metadata.get("price_numeric", 0)
                    }
                    
                    # Apply filters manually
                    if category_filter and service.get("category") != category_filter:
                        continue
                    
                    if location_filter and location_filter.lower() not in service.get("location", "").lower():
                        continue
                    
                    if max_price is not None and service.get("price_numeric", 0) > max_price:
                        continue
                    
                    services.append(service)
                    
                    # Stop if we have enough results
                    if len(services) >= n_results:
                        break
            
            print(f"🔍 Found {len(services)} services matching '{query}'")
            return services
            
        except Exception as e:
            print(f"❌ Error searching services: {str(e)}")
            return []
    
    def get_all_services(self) -> List[Dict[str, Any]]:
        """Get all services from the database"""
        try:
            results = self.collection.get()
            
            services = []
            if results['metadatas']:
                for metadata in results['metadatas']:
                    service = {
                        "name": metadata.get("name", ""),
                        "category": metadata.get("category", ""),
                        "address": metadata.get("address", ""),
                        "phone": metadata.get("phone", ""),
                        "rating": metadata.get("rating", ""),
                        "price": metadata.get("price", ""),
                        "location": metadata.get("location", ""),
                        "price_numeric": metadata.get("price_numeric", 0)
                    }
                    services.append(service)
            
            return services
            
        except Exception as e:
            print(f"❌ Error getting all services: {str(e)}")
            return []
    
    def get_categories(self) -> List[str]:
        """Get all unique categories in the database"""
        try:
            services = self.get_all_services()
            categories = list(set([service.get("category", "") for service in services if service.get("category")]))
            return sorted(categories)
        except Exception as e:
            print(f"❌ Error getting categories: {str(e)}")
            return []
    
    def get_locations(self) -> List[str]:
        """Get all unique locations in the database"""
        try:
            services = self.get_all_services()
            locations = list(set([service.get("location", "") for service in services if service.get("location")]))
            return sorted(locations)
        except Exception as e:
            print(f"❌ Error getting locations: {str(e)}")
            return []
    
    def _create_service_document(self, service: Dict[str, Any]) -> str:
        """Create a searchable document from service data"""
        parts = []
        
        if service.get("name"):
            parts.append(f"Service: {service['name']}")
        
        if service.get("category"):
            parts.append(f"Category: {service['category']}")
        
        if service.get("address"):
            parts.append(f"Address: {service['address']}")
        
        if service.get("rating"):
            parts.append(f"Rating: {service['rating']}")
        
        if service.get("price"):
            parts.append(f"Price: {service['price']}")
        
        return " | ".join(parts)
    
    def _extract_location(self, address: str) -> str:
        """Extract location from address"""
        if not address:
            return ""
        
        # Simple location extraction - can be improved
        parts = address.split(",")
        if len(parts) >= 2:
            return parts[-2].strip()  # Usually city is second to last
        return address.strip()
    
    def _extract_price_numeric(self, price: str) -> float:
        """Extract numeric price from price string"""
        if not price:
            return 0.0
        
        try:
            # Remove currency symbols and extract numbers
            import re
            numbers = re.findall(r'\d+', price.replace("₹", "").replace("Rs", "").replace(",", ""))
            if numbers:
                return float(numbers[0])
        except:
            pass
        
        return 0.0
    
    def load_from_json(self, json_file: str) -> bool:
        """Load services from JSON file into the database"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                services = json.load(f)
            
            return self.add_services(services)
            
        except Exception as e:
            print(f"❌ Error loading from JSON: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            services = self.get_all_services()
            categories = self.get_categories()
            locations = self.get_locations()
            
            return {
                "total_services": len(services),
                "categories": len(categories),
                "locations": len(locations),
                "category_list": categories,
                "location_list": locations
            }
        except Exception as e:
            print(f"❌ Error getting stats: {str(e)}")
            return {}

# Example usage
if __name__ == "__main__":
    # Initialize database
    db = ServiceVectorDB()
    
    # Load sample data if available
    if os.path.exists("sample_services.json"):
        print("📂 Loading sample data...")
        db.load_from_json("sample_services.json")
        
        # Get stats
        stats = db.get_stats()
        print(f"📊 Database stats: {stats}")
        
        # Test search
        results = db.search_services("AC repair", n_results=3)
        print(f"\n🔍 Search results for 'AC repair':")
        for i, service in enumerate(results, 1):
            print(f"{i}. {service['name']} - {service['price']} - {service['rating']}")
    else:
        print("❌ No sample data found. Run test_scraper.py first.")
