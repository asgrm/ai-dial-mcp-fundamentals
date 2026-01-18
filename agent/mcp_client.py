from typing import Optional, Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CallToolResult, TextContent, GetPromptResult, ReadResourceResult, Resource, TextResourceContents, BlobResourceContents, Prompt
from pydantic import AnyUrl


class MCPClient:
    """Handles MCP server connection and tool execution"""

    def __init__(self, mcp_server_url: str) -> None:
        self.mcp_server_url = mcp_server_url
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None

    async def __aenter__(self):
        #TODO:
        # 1. Call `streamablehttp_client` method with `mcp_server_url` and assign to `self._streams_context`
        self._streams_context = streamable_http_client(self.mcp_server_url)
        # 2. Call `await self._streams_context.__aenter__()` and assign to `read_stream, write_stream, _`
        read_stream, write_stream, _ = await self._streams_context.__aenter__()
        # 3. Create `ClientSession(read_stream, write_stream)` and assign to `self._session_context`
        self._session_context = ClientSession(read_stream, write_stream)
        # 4. Call `await self._session_context.__aenter__()` and assign it to `self.session`
        self.session = await self._session_context.__aenter__()
        # 5. Call `self.session.initialize()`, and print its result (to check capabilities of MCP server later)
        init_result = await self.session.initialize()

        print(init_result.model_dump_json(indent=2))
        # 6. return self
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
        tools = await self.session.list_tools()
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
            } for tool in tools.tools
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
        content = tool_result.content[0]
        # 3. print(f"    ⚙️: {content}\n")
        print(f"    ⚙️: {content}\n")
        # 4. If `isinstance(content, TextContent)` -> return content.text
        #    else -> return content
        if isinstance(content, TextContent):
            return content.text
        else:
            return content

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

    async def get_resource(self, uri: AnyUrl) -> str:
        """Get specific resource content"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        #TODO:
        # 1. Get resource by uri (uri is that we provided on the Server side "users-management://flow-diagram")
        # 2. Get contents of [0] resource
        # 3. ResourceContents has 2 types TextResourceContents and BlobResourceContents, in case if content is instance
        #    of TextResourceContents return it is `text`, in case of BlobResourceContents return it is `blob`
        # ---
        # Optional: Later on in app.py you can try to fetch resource and print it (in our case it is image/png provided
        # as bytes, but you can return on the server side some dict just to check how resources are looks like).
        resource_result: ReadResourceResult = await self.session.read_resource(uri)
        content = resource_result.contents[0]

        if isinstance(content, TextResourceContents):
            return content.text
        elif isinstance(content, BlobResourceContents):
            return content.blob


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



    async def get_prompt(self, name: str) -> str:
        """Get specific prompt content"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")
        #TODO:
        # 1. Get prompt by name
        prompt_result: GetPromptResult = await self.session.get_prompt(name)
        # 2. Create variable `combined_content` with empty string
        combined_content = ""
        # 3. Iterate through prompt result `messages` and:
        #       - if `message` has attribute 'content' and is instance of TextContent then concat `combined_content`
        #          with `message.content.text + "\n"`
        #       - if `message` has attribute 'content' and is instance of `str` then concat `combined_content` with
        #          with `message.content + "\n"`
        for message in prompt_result.messages:
            if hasattr(message, 'content') and isinstance(message.content, TextContent):
                combined_content += message.content.text + "\n"
            elif hasattr(message, 'content') and isinstance(message.content, str):
                combined_content += message.content + "\n"
        # 4. Return `combined_content`
        return combined_content.strip()
