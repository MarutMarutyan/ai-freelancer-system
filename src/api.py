"""HTTP API для интеграции с n8n."""

from fastapi import FastAPI
from sqlmodel import Session, select

from src.database.db import engine
from src.database.models import Order, Response

app = FastAPI(title="AI Freelancer API", docs_url=None, redoc_url=None)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/response")
def find_response(q: str = ""):
    """Найти отклик по ключевым словам из названия заказа."""
    if not q.strip():
        return {"found": False, "reason": "empty query"}

    words = [w.strip() for w in q.lower().split() if len(w.strip()) > 3]

    with Session(engine) as session:
        orders = session.exec(
            select(Order, Response)
            .join(Response, Order.id == Response.order_id)
            .order_by(Response.created_at.desc())
        ).all()

        if not orders:
            return {"found": False, "reason": "no responses in database"}

        best_score = 0
        best_order = None
        best_response = None

        for order, response in orders:
            title_lower = order.title.lower()
            score = sum(1 for w in words if w in title_lower)
            if score > best_score:
                best_score = score
                best_order = order
                best_response = response

        if best_score == 0 or best_order is None:
            order, response = orders[0]
            return {
                "found": True,
                "matched": False,
                "order_title": order.title,
                "proposal_text": response.final_text or response.draft_text,
                "proposed_price": response.proposed_price,
                "proposed_deadline": response.proposed_deadline,
                "note": "точного совпадения нет, взят последний отклик",
            }

        return {
            "found": True,
            "matched": True,
            "order_title": best_order.title,
            "proposal_text": best_response.final_text or best_response.draft_text,
            "proposed_price": best_response.proposed_price,
            "proposed_deadline": best_response.proposed_deadline,
        }
