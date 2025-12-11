"""Tests for pendo_tracker module."""
import pytest
from unittest import mock


@pytest.mark.asyncio
@mock.patch.dict("os.environ", {
    "PENDO_TRACK_EVENT_SECRET_KEY": "",
    "USER_ID": "test-user",
    "ORGANIZATION_NAME": "test-org",
    "STUDIO_ENV": "production",
})
async def test_track_pendo_event_without_key():
    """Test that tracking is skipped when API key is not configured."""
    # Import after patching env vars
    from mcp_server_civis.civis_studio_pendo_tracker import track_pendo_event

    with mock.patch("httpx.AsyncClient") as mock_client_class:
        # Should not raise an exception
        await track_pendo_event("test_event")
        
        # Verify HTTP client was never created
        mock_client_class.assert_not_called()


@pytest.mark.asyncio
@mock.patch.dict("os.environ", {
    "PENDO_TRACK_EVENT_SECRET_KEY": "test-key",
    "USER_ID": "test-user",
    "ORGANIZATION_NAME": "test-org",
    "STUDIO_ENV": "development",
})
async def test_track_pendo_event_in_dev():
    """Test that tracking is skipped in development environment."""
    # Import after patching env vars
    from mcp_server_civis.civis_studio_pendo_tracker import track_pendo_event

    with mock.patch("httpx.AsyncClient") as mock_client_class:
        # Should not make HTTP request in dev
        await track_pendo_event("test_event", {"prop": "value"})
        
        # Verify HTTP client was never created in non-production
        mock_client_class.assert_not_called()


@pytest.mark.asyncio
@mock.patch.dict("os.environ", {
    "PENDO_TRACK_EVENT_SECRET_KEY": "test-key",
    "USER_ID": "test-user",
    "ORGANIZATION_NAME": "test-org",
    "STUDIO_ENV": "production",
})
async def test_track_pendo_event_in_production():
    """Test that tracking sends HTTP request in production."""
    # Import after patching env vars
    from mcp_server_civis.civis_studio_pendo_tracker import track_pendo_event

    with mock.patch("httpx.AsyncClient") as mock_client_class:
        # Setup mock
        mock_client = mock.MagicMock()
        mock_response = mock.MagicMock()
        mock_response.raise_for_status = mock.MagicMock()

        # Setup async context manager
        mock_client.__aenter__ = mock.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mock.AsyncMock(return_value=None)
        mock_client.post = mock.AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        await track_pendo_event("test_event", {"tool_name": "run_query"})

        # Verify HTTP request was made
        assert mock_client.post.called
        call_kwargs = mock_client.post.call_args.kwargs

        # Check the event data structure
        event_json = call_kwargs['json']
        assert event_json['type'] == 'track'
        assert event_json['event'] == 'Civis Studio | MCP | test_event'
        assert event_json['visitorId'] == 'test-user'
        assert event_json['accountId'] == 'test-org'
        assert event_json['properties']['tool_name'] == 'run_query'

        # Check headers
        headers = call_kwargs['headers']
        assert headers['Content-Type'] == 'application/json'
        assert headers['x-pendo-integration-key'] == 'test-key'


@pytest.mark.asyncio
@mock.patch.dict("os.environ", {
    "PENDO_TRACK_EVENT_SECRET_KEY": "test-key",
    "USER_ID": "test-user",
    "ORGANIZATION_NAME": "test-org",
    "STUDIO_ENV": "production",
})
async def test_track_pendo_event_with_error():
    """Test that tracking handles HTTP errors gracefully."""
    # Import after patching env vars
    from mcp_server_civis.civis_studio_pendo_tracker import track_pendo_event

    with mock.patch("httpx.AsyncClient") as mock_client_class:
        # Setup mock to raise error
        mock_client = mock.MagicMock()
        mock_client.__aenter__ = mock.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mock.AsyncMock(return_value=None)
        mock_client.post = mock.AsyncMock(
            side_effect=Exception("Network error")
        )
        mock_client_class.return_value = mock_client

        # Should not raise exception, just log error
        await track_pendo_event("test_event")
