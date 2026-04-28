"""Appointment booking and management."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from database.models import Appointment, AppointmentStatus, Lead, Property


class AppointmentHandler:
    def __init__(self, db: Session) -> None:
        self.db = db

    def book(
        self,
        property_id: int,
        client_name: str,
        client_phone: str,
        scheduled_at: str,
        notes: str | None = None,
    ) -> str:
        # Verify property exists
        prop = self.db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return f"❌ Property #{property_id} not found."

        # Get or create lead
        lead = self.db.query(Lead).filter(Lead.phone == client_phone).first()
        if not lead:
            lead = Lead(phone=client_phone, name=client_name)
            self.db.add(lead)
            self.db.flush()
        elif not lead.name and client_name:
            lead.name = client_name

        # Parse datetime
        try:
            scheduled_dt = datetime.fromisoformat(scheduled_at)
        except ValueError:
            return "❌ Invalid date format. Please use: YYYY-MM-DDTHH:MM:SS"

        if scheduled_dt < datetime.utcnow():
            return "❌ Cannot book an appointment in the past."

        # Check for double-booking (same property, same hour)
        window_start = scheduled_dt - timedelta(minutes=30)
        window_end   = scheduled_dt + timedelta(minutes=30)
        conflict = (
            self.db.query(Appointment)
            .filter(
                Appointment.property_id == property_id,
                Appointment.status != AppointmentStatus.cancelled,
                Appointment.scheduled_at.between(window_start, window_end),
            )
            .first()
        )
        if conflict:
            return (
                "❌ That time slot is already booked for this property. "
                "Please choose another time (30 min gap required)."
            )

        appt = Appointment(
            lead_id     = lead.id,
            property_id = property_id,
            scheduled_at = scheduled_dt,
            notes       = notes,
        )
        self.db.add(appt)
        self.db.commit()
        self.db.refresh(appt)

        return (
            f"✅ *Viewing Booked!*\n\n"
            f"📍 {prop.title}\n"
            f"👤 {client_name}\n"
            f"📅 {scheduled_dt.strftime('%A, %d %B %Y at %I:%M %p')}\n"
            f"🔖 Booking ID: #{appt.id}\n\n"
            f"We'll send a reminder the day before. Reply *cancel #{appt.id}* to cancel."
        )

    def cancel(self, appointment_id: int, client_phone: str) -> str:
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            return f"Appointment #{appointment_id} not found."

        lead = self.db.query(Lead).filter(Lead.id == appt.lead_id).first()
        if lead and lead.phone != client_phone:
            return "❌ You can only cancel your own appointments."

        appt.status = AppointmentStatus.cancelled
        self.db.commit()
        return f"✅ Appointment #{appointment_id} has been cancelled."

    def list_appointments(self, date_filter: str = "today") -> str:
        now = datetime.utcnow()
        q = self.db.query(Appointment).filter(
            Appointment.status != AppointmentStatus.cancelled
        )

        if date_filter == "today":
            q = q.filter(
                Appointment.scheduled_at >= now.replace(hour=0, minute=0, second=0),
                Appointment.scheduled_at < now.replace(hour=23, minute=59, second=59),
            )
        elif date_filter == "tomorrow":
            tomorrow = now + timedelta(days=1)
            q = q.filter(
                Appointment.scheduled_at >= tomorrow.replace(hour=0, minute=0, second=0),
                Appointment.scheduled_at < tomorrow.replace(hour=23, minute=59, second=59),
            )
        elif date_filter == "this_week":
            q = q.filter(Appointment.scheduled_at >= now, Appointment.scheduled_at < now + timedelta(days=7))

        appts = q.order_by(Appointment.scheduled_at.asc()).all()
        if not appts:
            return f"No appointments for {date_filter}."

        lines = [f"*Appointments — {date_filter.replace('_', ' ').title()}* ({len(appts)})\n"]
        for a in appts:
            lead = self.db.query(Lead).filter(Lead.id == a.lead_id).first()
            prop = self.db.query(Property).filter(Property.id == a.property_id).first()
            lines.append(
                f"• {a.scheduled_at.strftime('%I:%M %p')} — "
                f"*{lead.name or lead.phone}* @ {prop.title if prop else '?'} "
                f"[#{a.id}]"
            )
        return "\n".join(lines)
