"""
Pendo tracking for MCP server usage analytics.
Similar to pendoTracker.js in civis-vscode.
"""
import os
import json
import sys
import time
from typing import Dict, Any, Optional
import httpx

PENDO_TRACK_URL = "https://app.pendo.io/data/track"


async def track_pendo_event(
    event_name: str,
    properties: Optional[Dict[str, Any]] = None
) -> None:
    """
    Send a track event to Pendo's server-side API.

    Args:
        event_name: Name of the event to track
        properties: Additional event properties (optional)
    """
    # Read environment variables at runtime to allow testing
    pendo_key = os.getenv("PENDO_TRACK_EVENT_SECRET_KEY", "77f7ac79-9151-4e5d-75a4-df191bee3e38")
    user_id = os.getenv("USER_ID", "unknown")
    org_name = os.getenv("ORGANIZATION_NAME", "unknown")
    studio_env = os.getenv("STUDIO_ENV", "production")

    if not pendo_key:
        print(
            f"[MCP Server] Pendo Track Secret not configured, "
            f"skipping event: {event_name}",
            file=sys.stderr
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

    print(f"[MCP Server] Event data: {json.dumps(event_data, indent=2)}", file=sys.stderr)

    if studio_env != "production":
        print(
            f"[MCP Server] Skipping pendo track event in non-production: {event_name}",
            file=sys.stderr
        )
        return

    print(f"[MCP Server] Sending pendo event to Pendo...", file=sys.stderr)
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
            print(f"[MCP Server] Pendo event sent successfully: {event_name}", file=sys.stderr)
            print(f"[MCP Server] Response: {response.status_code}", file=sys.stderr)
    except Exception as error:
        print(f"[MCP Server] Error sending Pendo event: {error}", file=sys.stderr)
        print(f"[MCP Server] Failed event data: {json.dumps(event_data, indent=2)}", file=sys.stderr)
