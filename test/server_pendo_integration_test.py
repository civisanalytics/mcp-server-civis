"""Integration tests for Pendo tracking in server.py."""
import pytest
from unittest import mock


@pytest.mark.asyncio
@mock.patch.dict("os.environ", {
    "PENDO_TRACK_EVENT_SECRET_KEY": "test-key",
    "USER_ID": "test-user",
    "ORGANIZATION_NAME": "test-org",
    "STUDIO_ENV": "production",
})
@mock.patch("mcp_server_civis.server.log_pendo_configuration")
@mock.patch("mcp_server_civis.server.track_pendo_event")
@mock.patch("mcp_server_civis.server.civis.APIClient")
async def test_pendo_tracking_on_startup(
    mock_api_client, mock_track_event, mock_log_config
):
    """Test that Pendo configuration is logged and session start is tracked."""
    from mcp_server_civis.server import serve

    # Mock the API client and its methods
    mock_client_instance = mock.MagicMock()
    mock_client_instance.default_database_credential_id = 1
    mock_db = mock.MagicMock()
    mock_db.id = 123
    mock_client_instance.databases.list.return_value = [mock_db]
    mock_api_client.return_value = mock_client_instance

    # Mock stdio_server to avoid actual server run
    with mock.patch("mcp_server_civis.server.stdio_server") as mock_stdio:
        mock_stdio.return_value.__aenter__ = mock.AsyncMock(
            return_value=(None, None)
        )
        mock_stdio.return_value.__aexit__ = mock.AsyncMock(return_value=None)

        # Mock server.run to avoid blocking
        with mock.patch("mcp_server_civis.server.Server.run") as mock_run:
            mock_run.return_value = None

            await serve(api_key="test-key", schema=None, description=None)

            # Verify log_pendo_configuration was called once
            mock_log_config.assert_called_once()

            # Verify track_pendo_event was called with session_started
            mock_track_event.assert_called_once_with(
                "session_started",
                {"schema": "none", "has_description": False}
            )


@pytest.mark.asyncio
@mock.patch.dict("os.environ", {
    "PENDO_TRACK_EVENT_SECRET_KEY": "test-key",
    "USER_ID": "test-user",
    "ORGANIZATION_NAME": "test-org",
    "STUDIO_ENV": "production",
})
@mock.patch("mcp_server_civis.server.track_pendo_event")
@mock.patch("mcp_server_civis.server.civis.APIClient")
async def test_pendo_tracking_on_tool_call(mock_api_client, mock_track_event):
    """Test that Pendo tracks when a tool is called."""
    from mcp_server_civis.server import serve

    # Mock the API client and its methods
    mock_client_instance = mock.MagicMock()
    mock_client_instance.default_database_credential_id = 1
    mock_db = mock.MagicMock()
    mock_db.id = 123
    mock_client_instance.databases.list.return_value = [mock_db]
    mock_client_instance.users.list_me.return_value = {"id": 1, "name": "test"}
    mock_api_client.return_value = mock_client_instance

    call_tool_handler = None

    # Capture the call_tool handler
    def capture_handler(func):
        nonlocal call_tool_handler
        call_tool_handler = func
        return func

    with mock.patch("mcp_server_civis.server.log_pendo_configuration"):
        with mock.patch("mcp_server_civis.server.stdio_server") as mock_stdio:
            mock_stdio.return_value.__aenter__ = mock.AsyncMock(
                return_value=(None, None)
            )
            mock_stdio.return_value.__aexit__ = mock.AsyncMock(
                return_value=None
            )

            with mock.patch("mcp_server_civis.server.Server") as mock_server:
                mock_server_instance = mock.MagicMock()
                mock_server.return_value = mock_server_instance
                mock_server_instance.call_tool.return_value = capture_handler
                mock_server_instance.list_tools.return_value = lambda x: x
                mock_server_instance.run = mock.AsyncMock()

                await serve(api_key="test-key", schema=None, description=None)

                # Simulate calling a tool
                if call_tool_handler:
                    await call_tool_handler("get_user", {})

                    # Verify track_pendo_event was called for tool invocation
                    # First call is session_started, second is tool_invoked
                    assert mock_track_event.call_count >= 2
                    tool_call = [
                        call for call in mock_track_event.call_args_list
                        if call[0][0] == "tool_invoked"
                    ]
                    assert len(tool_call) == 1
                    assert tool_call[0][0][1] == {"tool_name": "get_user"}
