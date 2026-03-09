"""
Firebase database & backend utilities for AlphaEdge.

Uses firebase-admin SDK for Firestore (NoSQL) and optionally
Realtime Database. Falls back gracefully if Firebase is not configured.
"""

import json
from typing import Any, Optional
from alphaedge.config import settings
from alphaedge.logger import log

_db = None
_app = None


def _init_firebase():
    """Initialise Firebase Admin SDK (once)."""
    global _app, _db
    if _app is not None:
        return _db

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if settings.firebase_credentials_path:
            cred = credentials.Certificate(settings.firebase_credentials_path)
        elif settings.firebase_credentials_json:
            info = json.loads(settings.firebase_credentials_json)
            cred = credentials.Certificate(info)
        else:
            # Use Application Default Credentials (ADC) — works on GCP
            cred = credentials.ApplicationDefault()

        _app = firebase_admin.initialize_app(
            cred,
            {
                "projectId": settings.firebase_project_id,
            },
        )
        _db = firestore.client()
        log.info(f"Firebase Firestore initialised (project: {settings.firebase_project_id})")
    except Exception as e:
        log.warning(f"Firebase init failed — running without persistent DB: {e}")
        _db = None

    return _db


def get_firestore():
    """Return Firestore client (lazy-init)."""
    if _db is None:
        _init_firebase()
    return _db


# ── CRUD helpers ─────────────────────────────────────────────────


def save_document(collection: str, doc_id: str, data: dict[str, Any]) -> bool:
    """Upsert a document in Firestore."""
    db = get_firestore()
    if db is None:
        log.debug(f"Firestore unavailable — skipping save to {collection}/{doc_id}")
        return False
    try:
        db.collection(collection).document(doc_id).set(data, merge=True)
        return True
    except Exception as e:
        log.error(f"Firestore save error ({collection}/{doc_id}): {e}")
        return False


def get_document(collection: str, doc_id: str) -> Optional[dict]:
    """Fetch a single document."""
    db = get_firestore()
    if db is None:
        return None
    try:
        doc = db.collection(collection).document(doc_id).get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        log.error(f"Firestore get error ({collection}/{doc_id}): {e}")
        return None


def query_collection(
    collection: str,
    field: Optional[str] = None,
    op: str = "==",
    value: Any = None,
    order_by: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    """Query documents from a Firestore collection."""
    db = get_firestore()
    if db is None:
        return []
    try:
        ref = db.collection(collection)
        if field and value is not None:
            ref = ref.where(field, op, value)
        if order_by:
            from google.cloud.firestore_v1 import Query

            ref = ref.order_by(order_by, direction=Query.DESCENDING)
        docs = ref.limit(limit).stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]
    except Exception as e:
        log.error(f"Firestore query error ({collection}): {e}")
        return []


def delete_document(collection: str, doc_id: str) -> bool:
    """Delete a document."""
    db = get_firestore()
    if db is None:
        return False
    try:
        db.collection(collection).document(doc_id).delete()
        return True
    except Exception as e:
        log.error(f"Firestore delete error ({collection}/{doc_id}): {e}")
        return False


def check_connection() -> bool:
    """Return True if Firestore is reachable."""
    db = get_firestore()
    if db is None:
        return False
    try:
        # Attempt a lightweight read
        list(db.collection("_health").limit(1).stream())
        return True
    except Exception:
        return False


# ── Prediction storage helpers ───────────────────────────────────


def save_prediction(ticker: str, prediction: dict) -> bool:
    """Persist a prediction result to Firestore."""
    from datetime import datetime

    doc_id = f"{ticker}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    data = {
        "ticker": ticker,
        "timestamp": datetime.utcnow().isoformat(),
        **prediction,
    }
    return save_document("predictions", doc_id, data)


def get_prediction_history(ticker: str, limit: int = 50) -> list[dict]:
    """Get recent predictions for a ticker."""
    return query_collection(
        "predictions",
        field="ticker",
        op="==",
        value=ticker,
        order_by="timestamp",
        limit=limit,
    )


def save_backtest_result(ticker: str, strategy: str, result: dict) -> bool:
    """Persist a backtest result."""
    from datetime import datetime

    doc_id = f"{ticker}_{strategy}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    data = {
        "ticker": ticker,
        "strategy": strategy,
        "timestamp": datetime.utcnow().isoformat(),
        **result,
    }
    return save_document("backtest_results", doc_id, data)


def save_user_portfolio(user_id: str, portfolio: list[dict]) -> bool:
    """Save a user's portfolio holdings to Firestore."""
    return save_document("portfolios", user_id, {"holdings": portfolio})


def get_user_portfolio(user_id: str) -> Optional[list[dict]]:
    """Retrieve a user's portfolio."""
    doc = get_document("portfolios", user_id)
    return doc.get("holdings", []) if doc else None
