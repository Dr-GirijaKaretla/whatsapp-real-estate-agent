"""
FAQ handler — answers agency policy questions.

In production this can be backed by a vector store (RAG) over uploaded
policy documents. For now it uses a curated list of common real estate
FAQs as fallback, and attempts a semantic match.
"""

from __future__ import annotations

import os

from sqlalchemy.orm import Session


STATIC_FAQS = {
    "commission": (
        "Our agency charges a standard commission of 2-3% of the property sale price "
        "for sellers, and typically 1 month's rent for rental placements."
    ),
    "process buy": (
        "Buying process:\n"
        "1️⃣ Share your requirements with us\n"
        "2️⃣ We shortlist properties\n"
        "3️⃣ Property viewings\n"
        "4️⃣ Make an offer\n"
        "5️⃣ Legal due diligence & documentation\n"
        "6️⃣ Payment & registration\n"
        "Typical timeline: 4-8 weeks."
    ),
    "process rent": (
        "Renting process:\n"
        "1️⃣ Share your preferences & budget\n"
        "2️⃣ View shortlisted properties\n"
        "3️⃣ Sign tenancy agreement\n"
        "4️⃣ Pay security deposit (usually 1-2 months rent)\n"
        "5️⃣ Move in!\n"
        "Typical timeline: 1-2 weeks."
    ),
    "documents": (
        "Documents typically needed:\n"
        "• Valid ID (passport / national ID)\n"
        "• Proof of income / bank statement\n"
        "• Employment letter (for rentals)\n"
        "• Tax returns (for purchase loans)\n"
        "Our team will guide you through the specific requirements."
    ),
    "loan mortgage": (
        "We work with partner banks to help you secure home loans. "
        "Typical loan-to-value ratio is 75-80% for buyers. "
        "Interest rates and eligibility depend on your profile. "
        "Ask us for a free consultation."
    ),
    "contact human agent": (
        "You can reach our team directly at:\n"
        f"📞 {os.getenv('AGENCY_PHONE', '+1 (800) 000-0000')}\n"
        f"📧 {os.getenv('AGENCY_EMAIL', 'info@yourrealestate.com')}\n"
        "Office hours: Mon–Sat, 9am–6pm"
    ),
}


class FAQHandler:
    def __init__(self, db: Session) -> None:
        self.db = db

    def answer(self, question: str) -> str:
        q = question.lower()

        for keyword, answer in STATIC_FAQS.items():
            if any(kw in q for kw in keyword.split()):
                return answer

        return (
            "That's a great question! Our team will get back to you with the "
            "exact details. In the meantime, feel free to ask me about available "
            "properties, viewings, or our buying/renting process."
        )
