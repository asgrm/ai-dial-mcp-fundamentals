import asyncio
import json
import os

from mcp import Resource
from mcp.types import Prompt

from agent.mcp_client import MCPClient
from agent.dial_client import DialClient
from agent.models.message import Message, Role
from agent.prompts import SYSTEM_PROMPT
from agent.constants import DIAL_ENDPOINT, API_KEY

# https://remote.mcpservers.org/fetch/mcp
# Pay attention that `fetch` doesn't have resources and prompts

async def main():

    # 1. Create MCP client with `docker_image="mcp/duckduckgo:latest"` as `mcp_client`
    async with MCPClient(docker_image="mcp/duckduckgo:latest") as mcp_client:
    # 2. Get Available MCP Tools, assign to `tools` variable, print tool as well
        tools = await mcp_client.get_tools()
        for tool in tools:
            print(tool)

        print("\n=== Available Prompts ===")
        prompts= await mcp_client.get_prompts()
        for prompt in prompts:
            print(prompt)
            content = await mcp_client.get_prompt(prompt.name)
            print(content)

    # 3. Create DialClient:
    #       - api_key=os.getenv("DIAL_API_KEY")
    #       - endpoint="https://ai-proxy.lab.epam.com"
    #       - tools=tools
    #       - mcp_client=mcp_client

        dial_client = DialClient(
            api_key=API_KEY,
            endpoint=DIAL_ENDPOINT,
            tools=tools,
            mcp_client=mcp_client
        )
    # 4. Create list with messages and add there SYSTEM_PROMPT with instructions to LLM
        messages = []
        print("MCP-based Agent is ready! Type your query or 'exit' to exit.")
    # 5. Create console chat (infinite loop + ability to exit from chat + preserve message history after the call to dial client)
        while True:
            user_input = input("\n> ").strip()
            if user_input.lower() == 'exit':
                break

            messages.append(
                Message(
                    role=Role.USER,
                    content=user_input
                )
            )

            ai_message: Message = await dial_client.get_completion(messages)
            messages.append(ai_message)

if __name__ == "__main__":
    asyncio.run(main())
