import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

from database import create_document, get_documents, db
from schemas import Booking

app = FastAPI(title="Golden Carthage / Golden Tulip Gammarth API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Golden Carthage / Golden Tulip Gammarth API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

@app.post("/api/book")
def create_booking(booking: Booking):
    try:
        if booking.check_out <= booking.check_in:
            raise HTTPException(status_code=400, detail="Check-out must be after check-in")
        nights = (booking.check_out - booking.check_in).days
        data = booking.model_dump()
        data.update({
            "nights": nights,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        })
        booking_id = create_document("booking", data)
        return {"success": True, "booking_id": booking_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rooms")
def list_rooms():
    """Static room list for UI filtering; details can be localized on frontend"""
    return [
        {"id": "deluxe", "name": "Deluxe Sea View", "beds": "King", "size": 32, "max": 3},
        {"id": "suite", "name": "Junior Suite", "beds": "King + Sofa", "size": 48, "max": 3},
        {"id": "family", "name": "Family Room", "beds": "2 Queen", "size": 44, "max": 4},
        {"id": "presidential", "name": "Presidential Suite", "beds": "King", "size": 120, "max": 4}
    ]

@app.get("/api/reviews")
def reviews():
    return {
        "tripadvisor": {
            "rating": 4.6,
            "count": 1248
        },
        "google": {
            "rating": 4.5,
            "count": 2380
        }
    }

class ChatRequest(BaseModel):
    message: str
    lang: str = "en"

@app.post("/api/concierge")
def concierge(req: ChatRequest):
    """Simple rule-based concierge stub to keep demo fast and private. Replace with real LLM later."""
    responses: Dict[str, Dict[str, str]] = {
        "en": {
            "greet": "Welcome to Golden Carthage. How may I assist with your stay?",
            "spa": "Our spa is open 9am–9pm with signature Mediterranean rituals.",
            "book": "You can book instantly via the bar above. Would you like recommendations?"
        },
        "fr": {
            "greet": "Bienvenue au Golden Carthage. Comment puis-je vous aider?",
            "spa": "Notre spa est ouvert de 9h à 21h avec des rituels méditerranéens.",
            "book": "Vous pouvez réserver via la barre ci-dessus. Voulez-vous des recommandations?"
        },
        "ar": {
            "greet": "مرحباً بكم في جولدن قرطاج. كيف يمكنني المساعدة؟",
            "spa": "السبا مفتوح من 9 صباحاً إلى 9 مساءً مع طقوس متوسطية.",
            "book": "يمكنكم الحجز مباشرة عبر الشريط أعلاه. هل ترغبون في توصيات؟"
        }
    }
    lang = req.lang if req.lang in responses else "en"
    text = req.message.lower()
    if any(k in text for k in ["spa", "massage", "wellness", "سبا", "مساج", "spa"]):
        key = "spa"
    elif any(k in text for k in ["book", "reserve", "reservation", "réserver", "حجز"]):
        key = "book"
    else:
        key = "greet"
    return {"reply": responses[lang][key]}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
