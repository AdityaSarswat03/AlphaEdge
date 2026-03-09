"""
Cloudflare DNS & CDN management utilities for AlphaEdge.

Provides helpers for:
 - Creating / updating DNS records (A, CNAME, AAAA)
 - Purging cache
 - Checking domain status

Requires CLOUDFLARE_API_TOKEN and CLOUDFLARE_ZONE_ID in .env.
"""

import httpx
from typing import Optional
from alphaedge.config import settings
from alphaedge.logger import log

CF_API = "https://api.cloudflare.com/client/v4"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.cloudflare_api_token}",
        "Content-Type": "application/json",
    }


def _zone_url(path: str = "") -> str:
    return f"{CF_API}/zones/{settings.cloudflare_zone_id}{path}"


# ── DNS records ──────────────────────────────────────────────────


def list_dns_records(record_type: Optional[str] = None, name: Optional[str] = None) -> list[dict]:
    """List DNS records for the zone, optionally filtered."""
    if not settings.cloudflare_api_token or not settings.cloudflare_zone_id:
        log.warning("Cloudflare not configured")
        return []
    params = {}
    if record_type:
        params["type"] = record_type
    if name:
        params["name"] = name
    try:
        resp = httpx.get(_zone_url("/dns_records"), headers=_headers(), params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("result", [])
    except Exception as e:
        log.error(f"Cloudflare list DNS error: {e}")
        return []


def upsert_dns_record(
    record_type: str,
    name: str,
    content: str,
    proxied: bool = True,
    ttl: int = 1,  # 1 = automatic
) -> Optional[dict]:
    """
    Create or update a DNS record.

    If a record with the same type+name already exists, it is updated.
    """
    if not settings.cloudflare_api_token or not settings.cloudflare_zone_id:
        log.warning("Cloudflare not configured — skipping DNS upsert")
        return None

    existing = list_dns_records(record_type=record_type, name=name)
    payload = {
        "type": record_type,
        "name": name,
        "content": content,
        "proxied": proxied,
        "ttl": ttl,
    }
    try:
        if existing:
            record_id = existing[0]["id"]
            resp = httpx.put(
                _zone_url(f"/dns_records/{record_id}"),
                headers=_headers(),
                json=payload,
                timeout=15,
            )
        else:
            resp = httpx.post(
                _zone_url("/dns_records"),
                headers=_headers(),
                json=payload,
                timeout=15,
            )
        resp.raise_for_status()
        result = resp.json().get("result", {})
        log.info(f"DNS {'updated' if existing else 'created'}: {record_type} {name} → {content}")
        return result
    except Exception as e:
        log.error(f"Cloudflare DNS upsert error: {e}")
        return None


def delete_dns_record(record_id: str) -> bool:
    """Delete a DNS record by ID."""
    try:
        resp = httpx.delete(
            _zone_url(f"/dns_records/{record_id}"),
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        log.error(f"Cloudflare DNS delete error: {e}")
        return False


# ── Cache management ─────────────────────────────────────────────


def purge_cache(files: Optional[list[str]] = None) -> bool:
    """
    Purge Cloudflare cache.

    If `files` is provided, only those URLs are purged.
    Otherwise, purges everything.
    """
    if not settings.cloudflare_api_token or not settings.cloudflare_zone_id:
        return False
    try:
        payload = {"files": files} if files else {"purge_everything": True}
        resp = httpx.post(
            _zone_url("/purge_cache"),
            headers=_headers(),
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        log.info(f"Cloudflare cache purged ({'selective' if files else 'full'})")
        return True
    except Exception as e:
        log.error(f"Cloudflare cache purge error: {e}")
        return False


# ── Zone info ────────────────────────────────────────────────────


def get_zone_info() -> Optional[dict]:
    """Return basic zone info (status, name servers, etc.)."""
    if not settings.cloudflare_api_token or not settings.cloudflare_zone_id:
        return None
    try:
        resp = httpx.get(_zone_url(), headers=_headers(), timeout=15)
        resp.raise_for_status()
        return resp.json().get("result")
    except Exception as e:
        log.error(f"Cloudflare zone info error: {e}")
        return None


def check_domain_status() -> str:
    """Quick check: returns 'active', 'pending', or 'error'."""
    info = get_zone_info()
    if info is None:
        return "not_configured"
    return info.get("status", "unknown")


# ── Convenience: setup AlphaEdge DNS ─────────────────────────────


def setup_alphaedge_dns(server_ip: str) -> dict:
    """
    One-shot helper to configure DNS records for AlphaEdge:
      - api.alphaedge.ai   → A record → server_ip
      - app.alphaedge.ai   → A record → server_ip
      - alphaedge.ai       → A record → server_ip
    """
    domain = settings.domain_name
    results = {}
    for subdomain in [settings.api_subdomain, settings.dashboard_subdomain, "@"]:
        name = f"{subdomain}.{domain}" if subdomain != "@" else domain
        r = upsert_dns_record("A", name, server_ip, proxied=True)
        results[name] = "ok" if r else "failed"
    return results
