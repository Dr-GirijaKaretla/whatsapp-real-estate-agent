"""
Claude tool definitions for the Real Estate Agent.

Each entry in TOOLS is passed directly to the Anthropic API.
The matching Python functions are in handlers/.
"""

TOOLS = [
    {
        "name": "search_properties",
        "description": (
            "Search the property database based on client requirements. "
            "Returns up to 5 matching listings."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_type": {
                    "type": "string",
                    "enum": ["sale", "rent", "both"],
                    "description": "Whether the client wants to buy or rent.",
                },
                "property_type": {
                    "type": "string",
                    "enum": ["apartment", "house", "villa", "commercial", "land", "office"],
                    "description": "Type of property.",
                },
                "city": {"type": "string", "description": "City name."},
                "area": {"type": "string", "description": "Neighbourhood or locality."},
                "min_bedrooms": {"type": "integer", "description": "Minimum number of bedrooms."},
                "max_bedrooms": {"type": "integer", "description": "Maximum number of bedrooms."},
                "min_price": {"type": "number", "description": "Minimum price / rent."},
                "max_price": {"type": "number", "description": "Maximum price / rent."},
                "furnished": {
                    "type": "string",
                    "enum": ["unfurnished", "semi", "fully"],
                    "description": "Furnishing status.",
                },
                "limit": {
                    "type": "integer",
                    "default": 3,
                    "description": "Max results to return (1-5).",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_property_details",
        "description": "Get the full details of a single property by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "integer",
                    "description": "The numeric ID of the property.",
                },
            },
            "required": ["property_id"],
        },
    },
    {
        "name": "book_appointment",
        "description": (
            "Book a property viewing appointment for the client. "
            "Requires client name, phone number, property ID, and preferred datetime."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "property_id": {"type": "integer"},
                "client_name": {"type": "string"},
                "client_phone": {"type": "string"},
                "scheduled_at": {
                    "type": "string",
                    "description": "ISO 8601 datetime string, e.g. '2025-06-15T10:00:00'.",
                },
                "notes": {"type": "string", "description": "Any special notes for the visit."},
            },
            "required": ["property_id", "client_name", "client_phone", "scheduled_at"],
        },
    },
    {
        "name": "save_lead",
        "description": (
            "Save or update a client's requirements and contact info as a lead. "
            "Call this once you have collected enough info from the client."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "phone": {"type": "string"},
                "name": {"type": "string"},
                "email": {"type": "string"},
                "intent": {"type": "string", "enum": ["buy", "rent"]},
                "preferred_type": {"type": "string"},
                "preferred_city": {"type": "string"},
                "preferred_area": {"type": "string"},
                "min_budget": {"type": "number"},
                "max_budget": {"type": "number"},
                "min_bedrooms": {"type": "integer"},
                "notes": {"type": "string"},
            },
            "required": ["phone"],
        },
    },
    {
        "name": "get_appointments",
        "description": "List today's or upcoming appointments. Admin-only.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_filter": {
                    "type": "string",
                    "enum": ["today", "tomorrow", "this_week", "all"],
                    "default": "today",
                },
            },
        },
    },
    {
        "name": "get_leads_summary",
        "description": "Get a summary of all leads with their statuses. Admin-only.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "enum": ["new", "contacted", "qualified", "viewing", "negotiating", "closed", "lost", "all"],
                    "default": "all",
                },
            },
        },
    },
    {
        "name": "add_property",
        "description": "Add a new property listing to the database. Admin-only.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":         {"type": "string"},
                "description":   {"type": "string"},
                "property_type": {"type": "string", "enum": ["apartment", "house", "villa", "commercial", "land", "office"]},
                "listing_type":  {"type": "string", "enum": ["sale", "rent", "both"]},
                "address":       {"type": "string"},
                "city":          {"type": "string"},
                "area":          {"type": "string"},
                "bedrooms":      {"type": "integer"},
                "bathrooms":     {"type": "integer"},
                "area_sqft":     {"type": "number"},
                "price":         {"type": "number"},
                "price_unit":    {"type": "string", "enum": ["total", "per_month", "per_sqft"]},
                "furnished":     {"type": "string", "enum": ["unfurnished", "semi", "fully"]},
                "parking":       {"type": "boolean"},
                "amenities":     {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "property_type", "listing_type", "price"],
        },
    },
    {
        "name": "answer_faq",
        "description": (
            "Answer questions about agency policies, buying/renting process, fees, "
            "legal requirements, or any question that needs knowledge-base lookup."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The client's question."},
            },
            "required": ["question"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate the conversation to a human agent when the client requests it or the query is too complex.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string"},
                "client_phone": {"type": "string"},
                "client_name":  {"type": "string"},
            },
            "required": ["reason", "client_phone"],
        },
    },
]
