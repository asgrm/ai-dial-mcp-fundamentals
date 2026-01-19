from typing import Optional, Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolResult, TextContent, Resource, Prompt

class MCPClient:
    """Handles MCP server connection and tool execution"""

    def __init__(self, docker_image: str) -> None:
        self.docker_image = docker_image
        self.session: Optional[ClientSession] = None
        self._stdio_context = None
        self._session_context = None
        self._process = None

    async def __aenter__(self):
        # docker version
        server_params = StdioServerParameters(
            command="docker",
            args=["run", "--rm", "-i", self.docker_image]
        )
        # wsl version

        # server_params = StdioServerParameters(
        #     command="wsl",
        #     args=["docker", "run", "--rm", "-i", self.docker_image]
        # )

        print(f"Starting Docker container: {self.docker_image}")
        self._stdio_context = stdio_client(server_params)

        read_stream, write_stream = await self._stdio_context.__aenter__()
        print(
            "Docker container started. To check container use such command:\ndocker ps --filter 'ancestor=mcp/duckduckgo:latest'")

        self._session_context = ClientSession(read_stream, write_stream)
        self.session = await self._session_context.__aenter__()

        print("Initializing MCP session...")
        init_result = await self.session.initialize()
        print(f"Capabilities: {init_result.model_dump_json(indent=2)}")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        #TODO:
        # This is shutdown method.
        # If session is present and session context is present as well then shutdown the session context (__aexit__ method with params)
        if self.session and self._session_context:
            await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
        # If streams context is present then shutdown the streams context (__aexit__ method with params)
        if self._streams_context:
            await self._streams_context.__aexit__(exc_type, exc_val, exc_tb)

    async def get_tools(self) -> list[dict[str, Any]]:
        """Get available tools from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")
        #TODO:
        # 1. Call `await self.session.list_tools()` and assign to `tools`
        tools_result = await self.session.list_tools()
        print(f"Retrieved {len(tools_result.tools)} tools from MCP server")
        # 2. Return list with dicts with tool schemas. It should be provided according to DIAL specification
        #    https://dialx.ai/dial_api#operation/sendChatCompletionRequest (request -> tools)

        dial_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            } for tool in tools_result.tools
        ]
        return dial_tools

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Call a specific tool on the MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        #TODO:
        # 1. Call `await self.session.call_tool(tool_name, tool_args)` and assign to `tool_result: CallToolResult` variable
        print(f"Calling `{tool_name}` with {tool_args}")
        tool_result: CallToolResult = await self.session.call_tool(tool_name, tool_args)
        # 2. Get `content` with index `0` from `tool_result` and assign to `content` variable
        if not tool_result.content:
            return "No content returned from tool"

        content = tool_result.content[0]
        # 3. print(f"    ⚙️: {content}\n")
        print(f"    ⚙️: {content}\n")
        # 4. If `isinstance(content, TextContent)` -> return content.text
        #    else -> return content
        if isinstance(content, TextContent):
            return content.text
        else:
            return str(content)

    async def get_resources(self) -> list[Resource]:
        """Get available resources from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")
        #TODO:
        # Wrap into try/except (not all MCP servers have resources), get `list_resources` (it is async) and resources
        # from it. In case of error print error and return an empty array
        try:
            result = await self.session.list_resources()
            return result.resources
        except Exception as e:
            print(f"Server doesn't support list_resources: {e}")
            return []

    async def get_prompts(self) -> list[Prompt]:
        """Get available prompts from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")
        #TODO:
        # Wrap into try/except (not all MCP servers have prompts), get `list_prompts` (it is async) and prompts
        # from it. In case of error print error and return an empty array
        try:
            result = await self.session.list_prompts()
            return result.prompts
        except Exception as e:
            print(f"Server doesn't support get_prompts: {e}")
            return []
