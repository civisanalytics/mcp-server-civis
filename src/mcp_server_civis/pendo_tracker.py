"""
Pendo tracking for MCP server usage analytics.
Similar to pendoTracker.js in civis-vscode.
"""
import os
import json
import logging
import time
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

PENDO_TRACK_URL = "https://app.pendo.io/data/track"


async def track_pendo_event(event_name: str, properties: Optional[Dict[str, Any]] = None) -> None:
    """
    Send a track event to Pendo's server-side API.
    
    Args:
        event_name: Name of the event to track
        properties: Additional event properties (optional)
    """
    # Read environment variables at runtime to allow testing with mocked env vars
    pendo_key = os.getenv("PENDO_TRACK_EVENT_SECRET_KEY", "")
    user_id = os.getenv("USER_ID", "unknown")
    org_name = os.getenv("ORGANIZATION_NAME", "unknown")
    studio_env = os.getenv("STUDIO_ENV", "production")
    
    if not pendo_key:
        logger.warning(
            f"[MCP Server] Pendo Track Secret not configured, skipping event: {event_name}"
        )
        return

    if properties is None:
        properties = {}

    event_data = {
        "type": "track",
        "event": f"Civis Studio | MCP | {event_name}",
        "visitorId": user_id,
        "accountId": org_name,
        "timestamp": int(time.time() * 1000),  # milliseconds since epoch
        "properties": properties,
    }

    if studio_env != "production":
        logger.info(
            f"[MCP Server] Skipping pendo track event in non-production: {event_name}"
        )
        logger.debug(f"Event data: {json.dumps(event_data)}")
        return

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                PENDO_TRACK_URL,
                json=event_data,
                headers={
                    "Content-Type": "application/json",
                    "x-pendo-integration-key": pendo_key,
                },
            )
            response.raise_for_status()
            logger.info(f"[MCP Server] Pendo event sent successfully: {event_name}")
    except Exception as error:
        logger.error(f"[MCP Server] Error sending Pendo event: {error}")
