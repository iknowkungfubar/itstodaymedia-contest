"""MCP Server Manager — instantiates MCP ad-platform servers and routes calls.

Provides a singleton :class:`MCPServerManager` that creates server instances
from application settings and exposes them to the rest of the backend through
:meth:`list_servers`, :meth:`get_server`, and :meth:`call_tool`.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from app.config import settings

# ── Import the MCP server implementations ──────────────────────────────────
# The mcp-servers/ directory lives at the project root (next to backend/).
# Because the directory name contains a hyphen it cannot be imported as a
# regular Python package, so we add its path to sys.path and import modules
# by their bare name (same approach used inside the server files themselves).
# backend/app/services/mcp_manager.py  → 3× parent = backend/  → 4× parent = project root
_mcp_servers_dir = str(Path(__file__).resolve().parent.parent.parent.parent / "mcp-servers")
if _mcp_servers_dir not in sys.path:
    sys.path.insert(0, _mcp_servers_dir)

from base import BaseMCPServer, MCPRequest, MCPResponse  # noqa: E402
from google_ads import GoogleAdsMCPServer  # noqa: E402
from meta_ads import MetaAdsMCPServer  # noqa: E402

logger = logging.getLogger(__name__)


class MCPServerManager:
    """Manages MCP server instances and routes tool calls to them.

    Created once at import time as a module-level singleton so the same
    server instances are shared across all requests.
    """

    def __init__(self) -> None:
        self._servers: dict[str, BaseMCPServer] = {}
        self._init_servers()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_servers(self) -> None:
        """Instantiate each supported MCP ad-platform server.

        Credentials from ``settings`` are forwarded to the constructors.
        When a setting is empty (the default in development) a dummy value
        is substituted so the servers return mock data rather than refusing
        the request — the credentials check is intended for production use
        once real API integration is added.
        """
        # ── WARNING about mock credentials ──────────────────────────────
        # When credentials are empty the MCP servers return mock data.
        # This is intentional for development / demo mode, but MUST be
        # addressed before connecting to real ad platforms by setting the
        # corresponding environment variables.
        if not settings.meta_ads_access_token:
            logger.warning(
                "META_ADS_ACCESS_TOKEN is not set — Meta Ads MCP server will return mock data only"
            )
        meta = MetaAdsMCPServer(
            access_token=settings.meta_ads_access_token or "mock_token",
            ad_account_id=settings.meta_ads_ad_account_id or "mock_ad_account",
        )
        self._servers["meta-ads"] = meta

        if not settings.google_ads_developer_token:
            logger.warning(
                "Google Ads credentials are not set — Google Ads MCP server "
                "will return mock data only"
            )
        google = GoogleAdsMCPServer(
            developer_token=settings.google_ads_developer_token or "mock_dev_token",
            client_id=settings.google_ads_client_id or "mock_client_id",
            client_secret=settings.google_ads_client_secret or "mock_secret",
            refresh_token=settings.google_ads_refresh_token or "mock_refresh",
            login_customer_id=settings.google_ads_login_customer_id or "mock_customer",
        )
        self._servers["google-ads"] = google

        logger.info(
            "Initialised %d MCP server(s): %s",
            len(self._servers),
            ", ".join(self._servers),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_servers(self) -> list[dict[str, Any]]:
        """Return metadata, resources, and tools for every registered server."""
        return [
            {
                "name": server.name,
                "version": server.version,
                "resources": [r.model_dump() for r in server.get_resources()],
                "tools": [t.model_dump() for t in server.get_tools()],
            }
            for server in self._servers.values()
        ]

    def get_server(self, name: str) -> BaseMCPServer | None:
        """Look up a registered server by its ``name``."""
        return self._servers.get(name)

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> MCPResponse:
        """Execute a tool on a specific MCP server.

        Parameters
        ----------
        server_name:
            The server identifier (e.g. ``"meta-ads"``, ``"google-ads"``).
        tool_name:
            The tool to invoke on that server.
        arguments:
            Optional parameters forwarded to the tool.

        Returns
        -------
        MCPResponse
            The server's response, which may carry an ``error`` string.
        """
        server = self.get_server(server_name)
        if not server:
            return MCPResponse(
                id="error",
                error=f"Unknown MCP server: {server_name}",
            )

        request = MCPRequest(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments or {},
            },
        )
        return await server.handle_request(request)


# Module-level singleton — imported by routes and other services.
mcp_manager = MCPServerManager()
