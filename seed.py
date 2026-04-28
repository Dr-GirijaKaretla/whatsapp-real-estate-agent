"""
Seed the database with sample properties for testing.
Run once after deployment: visit /seed in your browser.
"""

from database import init_db, SessionLocal
from database.models import Property

SAMPLE_PROPERTIES = [
    {
        "title": "Modern 2BHK Apartment in Downtown",
        "description": "Bright and spacious apartment with stunning city views, open-plan kitchen, and premium finishes. Walking distance to shops and metro.",
        "property_type": "apartment",
        "listing_type": "rent",
        "address": "45 Main Street, Downtown",
        "city": "Miami",
        "area": "Downtown",
        "bedrooms": 2,
        "bathrooms": 2,
        "area_sqft": 950,
        "price": 2200,
        "price_unit": "per_month",
        "furnished": "fully",
        "parking": True,
        "amenities": ["gym", "pool", "concierge", "rooftop terrace"],
        "is_featured": True,
    },
    {
        "title": "Luxury 3BHK Villa with Pool",
        "description": "Stunning private villa in a gated community. Private pool, landscaped garden, double garage. Perfect for families.",
        "property_type": "villa",
        "listing_type": "sale",
        "address": "12 Palm Grove, Coral Gables",
        "city": "Miami",
        "area": "Coral Gables",
        "bedrooms": 3,
        "bathrooms": 3,
        "area_sqft": 2800,
        "price": 1250000,
        "price_unit": "total",
        "furnished": "semi",
        "parking": True,
        "amenities": ["private pool", "garden", "double garage", "smart home", "solar panels"],
        "is_featured": True,
    },
    {
        "title": "Cozy 1BHK Studio Near Beach",
        "description": "Perfect starter home or investment property. Steps from the beach, recently renovated, move-in ready.",
        "property_type": "apartment",
        "listing_type": "rent",
        "address": "8 Ocean Drive",
        "city": "Miami",
        "area": "South Beach",
        "bedrooms": 1,
        "bathrooms": 1,
        "area_sqft": 580,
        "price": 1600,
        "price_unit": "per_month",
        "furnished": "fully",
        "parking": False,
        "amenities": ["beach access", "balcony", "air conditioning"],
        "is_featured": False,
    },
    {
        "title": "Spacious 4BHK Family Home",
        "description": "Large family home in a quiet neighbourhood. Open-plan living, modern kitchen, big backyard. Top-rated schools nearby.",
        "property_type": "house",
        "listing_type": "sale",
        "address": "34 Maple Lane, Kendall",
        "city": "Miami",
        "area": "Kendall",
        "bedrooms": 4,
        "bathrooms": 3,
        "area_sqft": 3200,
        "price": 875000,
        "price_unit": "total",
        "furnished": "unfurnished",
        "parking": True,
        "amenities": ["backyard", "garage", "laundry room", "storage"],
        "is_featured": False,
    },
    {
        "title": "Prime Office Space in Brickell",
        "description": "Modern fitted office in Miami's financial district. Floor-to-ceiling windows, meeting rooms, reception area included.",
        "property_type": "office",
        "listing_type": "rent",
        "address": "100 Brickell Avenue, Suite 1500",
        "city": "Miami",
        "area": "Brickell",
        "bedrooms": None,
        "bathrooms": 2,
        "area_sqft": 1800,
        "price": 6500,
        "price_unit": "per_month",
        "furnished": "fully",
        "parking": True,
        "amenities": ["meeting rooms", "reception", "high-speed internet", "24/7 access", "parking"],
        "is_featured": False,
    },
    {
        "title": "Waterfront 2BHK Condo",
        "description": "Breathtaking water views from every room. Floor-to-ceiling windows, private balcony, resort-style amenities.",
        "property_type": "apartment",
        "listing_type": "both",
        "address": "1 Bayshore Drive",
        "city": "Miami",
        "area": "Coconut Grove",
        "bedrooms": 2,
        "bathrooms": 2,
        "area_sqft": 1100,
        "price": 750000,
        "price_unit": "total",
        "furnished": "semi",
        "parking": True,
        "amenities": ["waterfront", "pool", "gym", "spa", "private balcony", "concierge"],
        "is_featured": True,
    },
]


def seed_database():
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(Property).count()
        if existing > 0:
            return f"Database already has {existing} properties. Skipping seed."

        for data in SAMPLE_PROPERTIES:
            db.add(Property(**data))
        db.commit()
        return f"✅ Seeded {len(SAMPLE_PROPERTIES)} sample properties successfully!"
    except Exception as e:
        db.rollback()
        return f"❌ Seed failed: {e}"
    finally:
        db.close()


if __name__ == "__main__":
    print(seed_database())
