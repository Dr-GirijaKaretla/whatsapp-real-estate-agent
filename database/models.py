"""SQLAlchemy ORM models for the WhatsApp Real Estate Agent."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, JSON,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ─── Enums ────────────────────────────────────────────────────────────────────

class PropertyType(str, enum.Enum):
    apartment   = "apartment"
    house       = "house"
    villa       = "villa"
    commercial  = "commercial"
    land        = "land"
    office      = "office"


class ListingType(str, enum.Enum):
    sale  = "sale"
    rent  = "rent"
    both  = "both"


class LeadStatus(str, enum.Enum):
    new         = "new"
    contacted   = "contacted"
    qualified   = "qualified"
    viewing     = "viewing"
    negotiating = "negotiating"
    closed      = "closed"
    lost        = "lost"


class AppointmentStatus(str, enum.Enum):
    pending   = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


# ─── Models ───────────────────────────────────────────────────────────────────

class Property(Base):
    __tablename__ = "properties"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    title        = Column(String(200), nullable=False)
    description  = Column(Text)
    property_type = Column(Enum(PropertyType), nullable=False)
    listing_type  = Column(Enum(ListingType), nullable=False)

    # Location
    address      = Column(String(500))
    city         = Column(String(100))
    area         = Column(String(100))
    pincode      = Column(String(20))
    latitude     = Column(Float)
    longitude    = Column(Float)

    # Specs
    bedrooms     = Column(Integer)
    bathrooms    = Column(Integer)
    area_sqft    = Column(Float)
    floor        = Column(Integer)
    total_floors = Column(Integer)
    parking      = Column(Boolean, default=False)
    furnished    = Column(String(20))   # unfurnished / semi / fully

    # Pricing
    price        = Column(Float, nullable=False)
    price_unit   = Column(String(20), default="total")  # total / per_month / per_sqft

    # Media & extras
    amenities    = Column(JSON, default=list)   # ["gym", "pool", ...]
    images       = Column(JSON, default=list)   # list of URLs
    is_active    = Column(Boolean, default=True)
    is_featured  = Column(Boolean, default=False)

    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    appointments = relationship("Appointment", back_populates="property")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "property_type": self.property_type,
            "listing_type": self.listing_type,
            "address": self.address,
            "city": self.city,
            "area": self.area,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "area_sqft": self.area_sqft,
            "price": self.price,
            "price_unit": self.price_unit,
            "furnished": self.furnished,
            "parking": self.parking,
            "amenities": self.amenities or [],
            "images": self.images or [],
            "is_active": self.is_active,
            "is_featured": self.is_featured,
        }

    def short_summary(self) -> str:
        """One-line summary for WhatsApp listing."""
        price_str = f"${self.price:,.0f}" if self.price_unit == "total" else f"${self.price:,.0f}/mo"
        beds = f"{self.bedrooms}BHK " if self.bedrooms else ""
        return (
            f"*#{self.id} — {beds}{self.title}*\n"
            f"📍 {self.area or self.city}\n"
            f"📐 {self.area_sqft:.0f} sqft  |  💰 {price_str}\n"
            f"🏷️ {self.listing_type.upper()} | {self.property_type.capitalize()}"
        )


class Lead(Base):
    __tablename__ = "leads"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    phone        = Column(String(30), nullable=False, unique=True, index=True)
    name         = Column(String(150))
    email        = Column(String(200))
    status       = Column(Enum(LeadStatus), default=LeadStatus.new)

    # Preferences captured through conversation
    intent       = Column(String(10))   # buy / rent
    preferred_type = Column(String(50))
    preferred_city = Column(String(100))
    preferred_area = Column(String(100))
    min_budget   = Column(Float)
    max_budget   = Column(Float)
    min_bedrooms = Column(Integer)
    notes        = Column(Text)

    # Meta
    source       = Column(String(50), default="whatsapp")
    last_seen    = Column(DateTime, default=datetime.utcnow)
    created_at   = Column(DateTime, default=datetime.utcnow)

    # Relationships
    appointments = relationship("Appointment", back_populates="lead")
    conversations = relationship("Conversation", back_populates="lead")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "phone": self.phone,
            "name": self.name,
            "email": self.email,
            "status": self.status,
            "intent": self.intent,
            "preferred_type": self.preferred_type,
            "preferred_city": self.preferred_city,
            "max_budget": self.max_budget,
            "min_bedrooms": self.min_bedrooms,
        }


class Appointment(Base):
    __tablename__ = "appointments"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    lead_id      = Column(Integer, ForeignKey("leads.id"), nullable=False)
    property_id  = Column(Integer, ForeignKey("properties.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    status       = Column(Enum(AppointmentStatus), default=AppointmentStatus.pending)
    notes        = Column(Text)
    created_at   = Column(DateTime, default=datetime.utcnow)

    # Relationships
    lead         = relationship("Lead", back_populates="appointments")
    property     = relationship("Property", back_populates="appointments")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "property_id": self.property_id,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "status": self.status,
            "notes": self.notes,
        }


class Conversation(Base):
    """Stores last N messages per lead for agent memory."""
    __tablename__ = "conversations"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    lead_id    = Column(Integer, ForeignKey("leads.id"), nullable=False)
    role       = Column(String(20), nullable=False)   # user / assistant
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    lead       = relationship("Lead", back_populates="conversations")
