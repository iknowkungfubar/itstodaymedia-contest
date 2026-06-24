from __future__ import annotations

import json
import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MCPRequest(BaseModel):
    """MCP protocol request envelope."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    method: str
    params: dict[str, Any] = Field(default_factory=dict)


class MCPResponse(BaseModel):
    """MCP protocol response envelope."""

    id: str
    result: dict[str, Any] | None = None
    error: str | None = None


class MCPResource(BaseModel):
    """An MCP resource descriptor."""

    uri: str
    name: str
    description: str
    mime_type: str = "application/json"


class MCPTool(BaseModel):
    """An MCP tool descriptor."""

    name: str
    description: str
    input_schema: dict[str, Any]


class BaseMCPServer(ABC):
    """Abstract base class for MCP ad platform servers.

    Implements the Model Context Protocol for ad platform connectivity.
    """

    def __init__(self, name: str, version: str = "0.1.0") -> None:
        self.name = name
        self.version = version
        self._request_counter = 0

    @abstractmethod
    def get_resources(self) -> list[MCPResource]:
        """Return available resources from this platform."""
        ...

    @abstractmethod
    def get_tools(self) -> list[MCPTool]:
        """Return available tools for this platform."""
        ...

    @abstractmethod
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle an incoming MCP request."""
        ...

    async def process_request(self, raw_request: str) -> str:
        """Process a raw JSON request string and return JSON response."""
        try:
            data = json.loads(raw_request)
            request = MCPRequest(**data)
            response = await self.handle_request(request)
        except json.JSONDecodeError as e:
            response = MCPResponse(
                id="error",
                error=f"Invalid JSON: {e}",
            )
        except Exception as e:
            logger.exception("Error processing request")
            response = MCPResponse(
                id=getattr(request, "id", "error"),
                error=str(e),
            )
        return response.model_dump_json(exclude_none=True)

    async def sse_event_stream(self) -> AsyncGenerator[str, None]:
        """Generate SSE events for MCP protocol streaming."""
        # Initial endpoint event
        yield f"event: endpoint\ndata: {json.dumps({'version': self.version, 'name': self.name})}\n\n"

        # Resource update events
        for resource in self.get_resources():
            yield f"event: resource\ndata: {resource.model_dump_json()}\n\n"

        # Tool listing
        for tool in self.get_tools():
            yield f"event: tool\ndata: {tool.model_dump_json()}\n\n"
