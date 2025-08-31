from justdial_real_scraper import JustDialRealScraper
import json

def generate_comprehensive_real_data():
    """Generate comprehensive real-like data for the database"""
    scraper = JustDialRealScraper()
    
    # Categories and locations to scrape
    categories_locations = [
        ("AC Repair", "Hyderabad"),
        ("AC Repair", "Madhapur"),
        ("AC Repair", "Gachibowli"),
        ("Plumber", "Hyderabad"),
        ("Plumber", "Madhapur"),
        ("Plumber", "Kondapur"),
        ("Electrician", "Hyderabad"),
        ("Electrician", "Jubilee Hills"),
        ("Electrician", "Banjara Hills"),
        ("Restaurant", "Hyderabad"),
        ("Restaurant", "Jubilee Hills"),
        ("Restaurant", "Madhapur"),
        ("Restaurant", "Kukatpally"),
        ("Bike Service", "Hyderabad"),
        ("Bike Service", "Gachibowli"),
        ("Bike Service", "Miyapur"),
        ("Doctor", "Hyderabad"),
        ("Doctor", "Banjara Hills"),
        ("Doctor", "Madhapur"),
        ("Dentist", "Hyderabad"),
        ("Dentist", "Jubilee Hills"),
        ("Gym", "Hyderabad"),
        ("Gym", "Gachibowli"),
        ("Beauty Parlor", "Hyderabad"),
        ("Beauty Parlor", "Kondapur"),
        ("Lawyer", "Hyderabad"),
        ("CA", "Hyderabad"),
        ("Real Estate Agent", "Gachibowli"),
        ("Insurance Agent", "Begumpet"),
        ("Cafe", "Madhapur"),
        ("Cafe", "Hitech City")
    ]
    
    all_services = []
    
    print("🎯 Generating comprehensive real-like JustDial data...")
    print(f"📊 Will scrape {len(categories_locations)} category-location combinations")
    
    for i, (category, location) in enumerate(categories_locations, 1):
        print(f"\n[{i}/{len(categories_locations)}] 🔍 Scraping: {category} in {location}")
        
        try:
            # Get 3-5 services per category-location combination
            services = scraper.scrape_category_real(category, location, max_results=4)
            
            if services:
                all_services.extend(services)
                print(f"✅ Added {len(services)} services ({len(all_services)} total)")
                
                # Show sample
                for service in services[:2]:  # Show first 2
                    print(f"   • {service.get('name', 'N/A')} - {service.get('price', 'N/A')}")
            else:
                print(f"⚠️ No services found for {category} in {location}")
        
        except Exception as e:
            print(f"❌ Error scraping {category} in {location}: {str(e)}")
        
        # Small delay to be respectful
        import time
        time.sleep(0.5)
    
    print(f"\n🎉 Generated {len(all_services)} total real-like services!")
    
    # Save to comprehensive file
    with open('real_justdial_comprehensive.json', 'w', encoding='utf-8') as f:
        json.dump(all_services, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved comprehensive data to: real_justdial_comprehensive.json")
    
    # Show summary
    categories = {}
    locations = {}
    
    for service in all_services:
        cat = service.get('category', 'Unknown')
        loc = service.get('location', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
        locations[loc] = locations.get(loc, 0) + 1
    
    print(f"\n📊 Data Summary:")
    print(f"   Total Services: {len(all_services)}")
    print(f"   Categories: {len(categories)}")
    print(f"   Locations: {len(locations)}")
    
    print(f"\n🏷️ Categories:")
    for cat, count in sorted(categories.items()):
        print(f"   • {cat}: {count} services")
    
    print(f"\n📍 Locations:")
    for loc, count in sorted(locations.items()):
        print(f"   • {loc}: {count} services")
    
    return all_services

if __name__ == "__main__":
    generate_comprehensive_real_data()
