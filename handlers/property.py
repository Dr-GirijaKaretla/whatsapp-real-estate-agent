"""Property CRUD and search operations."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from database.models import Property, PropertyType, ListingType


class PropertyHandler:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search(
        self,
        listing_type: str | None = None,
        property_type: str | None = None,
        city: str | None = None,
        area: str | None = None,
        min_bedrooms: int | None = None,
        max_bedrooms: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        furnished: str | None = None,
        limit: int = 3,
    ) -> str:
        q = self.db.query(Property).filter(Property.is_active == True)

        if listing_type and listing_type != "both":
            q = q.filter(
                (Property.listing_type == listing_type) |
                (Property.listing_type == ListingType.both)
            )
        if property_type:
            q = q.filter(Property.property_type == property_type)
        if city:
            q = q.filter(Property.city.ilike(f"%{city}%"))
        if area:
            q = q.filter(Property.area.ilike(f"%{area}%"))
        if min_bedrooms is not None:
            q = q.filter(Property.bedrooms >= min_bedrooms)
        if max_bedrooms is not None:
            q = q.filter(Property.bedrooms <= max_bedrooms)
        if min_price is not None:
            q = q.filter(Property.price >= min_price)
        if max_price is not None:
            q = q.filter(Property.price <= max_price)
        if furnished:
            q = q.filter(Property.furnished == furnished)

        # Featured first
        q = q.order_by(Property.is_featured.desc(), Property.created_at.desc())
        properties = q.limit(min(limit, 5)).all()

        if not properties:
            return "No properties found matching your criteria."

        lines = [f"Found {len(properties)} propert{'y' if len(properties) == 1 else 'ies'}:\n"]
        for p in properties:
            lines.append(p.short_summary())
            lines.append("")
        lines.append("Reply with a property number (e.g. *#3*) for full details, or *book #3* to schedule a viewing.")
        return "\n".join(lines)

    def get_details(self, property_id: int) -> str:
        prop = self.db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return f"Property #{property_id} not found."

        d = prop.to_dict()
        amenities = ", ".join(d["amenities"]) if d["amenities"] else "None listed"
        price_label = (
            f"${d['price']:,.0f}" if d["price_unit"] == "total"
            else f"${d['price']:,.0f}/month"
        )
        beds = f"{d['bedrooms']} bed  |  " if d["bedrooms"] else ""
        baths = f"{d['bathrooms']} bath  |  " if d["bathrooms"] else ""

        return (
            f"*{d['title']}* (#{d['id']})\n\n"
            f"📍 {d['address'] or d['area']}, {d['city']}\n"
            f"🏠 {d['property_type'].capitalize()} — {d['listing_type'].upper()}\n"
            f"📐 {beds}{baths}{d['area_sqft'] or '?'} sqft\n"
            f"🛋️ {d['furnished'] or 'N/A'}  |  🚗 Parking: {'✅' if d['parking'] else '❌'}\n"
            f"💰 {price_label}\n\n"
            f"📝 {d['description'] or 'No description.'}\n\n"
            f"✨ Amenities: {amenities}\n\n"
            f"Reply *book #{d['id']}* to schedule a viewing."
        )

    def add(self, **kwargs: Any) -> str:
        prop = Property(**kwargs)
        self.db.add(prop)
        self.db.commit()
        self.db.refresh(prop)
        return f"✅ Property added! ID: #{prop.id} — {prop.title}"

    def update(self, property_id: int, **kwargs: Any) -> str:
        prop = self.db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return f"Property #{property_id} not found."
        for k, v in kwargs.items():
            setattr(prop, k, v)
        self.db.commit()
        return f"✅ Property #{property_id} updated."
