import asyncio
import os
import sys
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from fastmcp import Client
from google import genai
from google.genai import types
from google.genai.types import Tool, FunctionDeclaration
from google.genai.types import GenerateContentConfig
from dotenv import load_dotenv
import subprocess
from kokoro import KPipeline
import soundfile as sf
import time

load_dotenv()

class MCPClient:
    def __init__(self, history_length: int = 5):
        self.sessions: dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.history_length = history_length
        self.conversation_history = []
        self.pipeline = KPipeline(lang_code='a')
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found. Please add it to your .env file.")
        self.genai_client = genai.Client(api_key=gemini_api_key)
        
    def add_to_history(self, query: str, response: str):
        """Add a query-response pair to conversation history."""
        self.conversation_history.append({
            "query": query,
            "response": response,
            "timestamp": time.time()
        })
        
        # Keep only the last k interactions
        if len(self.conversation_history) > self.history_length:
            self.conversation_history = self.conversation_history[-self.history_length:]
    
    def get_history_context(self) -> str:
        """Format conversation history for inclusion in the prompt."""
        if not self.conversation_history:
            return ""
        
        history_text = "\n\nPrevious conversation:\n"
        for i, interaction in enumerate(self.conversation_history, 1):
            history_text += f"Q{i}: {interaction['query']}\n"
            history_text += f"A{i}: {interaction['response'][:200]}...\n"  # Truncate long responses
        history_text += "\n"
        
        return history_text
        
    async def connect_to_servers(self):
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        if not google_client_id or not google_client_secret:
            raise ValueError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET not found. "
                "Please add them to your .env file."
            )

        docker_args = [
            "run", "--rm", "-i",
            "-p", "8080:8080",
            "-v", f"{os.path.expanduser('~')}/.mcp/google-workspace-mcp:/app/config",
            "-v", f"{os.path.expanduser('~')}/Documents/workspace-mcp-files:/app/workspace",
            "-e", "GOOGLE_CLIENT_ID",
            "-e", "GOOGLE_CLIENT_SECRET",
            "-e", "LOG_MODE=strict",
            "google-workspace-mcp:local"
        ]

        # Get the absolute path to the server scripts
        server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'server'))

        server_configs = {
            "googletool": {
                "command": "docker",
                "args": docker_args,
                "env": {
                    "GOOGLE_CLIENT_ID": google_client_id,
                    "GOOGLE_CLIENT_SECRET": google_client_secret,
                }
            },
            "spotify": {"command": "python3", "args": [os.path.join(server_dir, "spotify-server.py")]},
            "terminal": {"command": "python3", "args": [os.path.join(server_dir, "terminal-server.py")]},
        }

        all_tools = []
        for name, config in server_configs.items():
            print(f"🚀 Starting and connecting to {name} server...")
            server_params = StdioServerParameters(
                command=config["command"], 
                args=config["args"],
                env=config.get("env")
            )
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            
            session = await self.exit_stack.enter_async_context(ClientSession(*stdio_transport))
            await session.initialize()
            
            self.sessions[name] = session
            
            response = await session.list_tools()
            
            # Add prefix to tool names
            for tool in response.tools:
                tool.name = f"{name}_{tool.name}"
            
            all_tools.extend(response.tools)
            print(f"✅ Connected to {name} server.")

        print("\n✅ Connected to all servers with tools:", [tool.name for tool in all_tools])
        self.function_declarations = convert_mcp_tools_to_gemini(all_tools)
        
    async def process_query(self, query: str) -> str:
        # tool/argument guide for Gemini
        tool_guide = "Available tools and their arguments:\n"
        for tool in self.function_declarations:
            for func in tool.function_declarations:
                # convert parameters to dict for compatibility
                if hasattr(func.parameters, 'model_dump'):
                    params_dict = func.parameters.model_dump()
                elif hasattr(func.parameters, 'dict'):
                    params_dict = func.parameters.dict()
                else:
                    params_dict = dict(func.parameters)
                params = params_dict.get('properties', {})
                param_list = ', '.join([f"'{k}'" for k in params.keys()])
                tool_guide += f"- {func.name}({param_list})\n"
        tool_guide += "\nUse these tools to answer the query. If a tool is needed, call it with the required parameters.\n If an error occurs, provide the error message and a traceback. \n\n"

        # Include conversation history in the prompt
        history_context = self.get_history_context()
        full_prompt = tool_guide + history_context + query

        user_prompt_content = types.Content(
            role='user',
            parts=[types.Part.from_text(text=full_prompt)]
        )
        
        # Initialize conversation contents with user prompt
        conversation_contents = [user_prompt_content]
        max_iterations = 3
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n🔄 Multi-step reasoning iteration {iteration}/{max_iterations}")
            
            # Generate response with current conversation context
            response = self.genai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=conversation_contents,
                config=types.GenerateContentConfig(
                    tools=self.function_declarations,
                ),
            )
            
            # Check if response has function calls
            has_function_call = False
            final_text = []
            
            for candidate in response.candidates:
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        if isinstance(part, types.Part):
                            if part.function_call:
                                has_function_call = True
                                function_call_part = part
                                
                                # Find the correct session and tool name
                                full_tool_name = function_call_part.function_call.name
                                session = None
                                server_name = None
                                original_tool_name = None

                                for s_name in self.sessions.keys():
                                    prefix = f"{s_name}_"
                                    if full_tool_name.startswith(prefix):
                                        session = self.sessions[s_name]
                                        server_name = s_name
                                        original_tool_name = full_tool_name[len(prefix):]
                                        break
                                
                                # If exact prefix match fails, search all func.name values
                                if not session:
                                    for s_name, sess in self.sessions.items():
                                        for tool in self.function_declarations:
                                            for func in tool.function_declarations:
                                                if func.name.endswith(full_tool_name):
                                                    session = sess
                                                    server_name = s_name
                                                    original_tool_name = full_tool_name
                                                    break
                                            if session:
                                                break
                                        if session:
                                            break
                                
                                if not session:
                                    raise ValueError(f"No server session found for tool call '{full_tool_name}'")

                                tool_name = original_tool_name
                                tool_args = function_call_part.function_call.args
                                
                                print(f"\n[Gemini requested tool call on '{server_name}': {tool_name} with args {tool_args}]")
                                try:
                                    result = await session.call_tool(tool_name, tool_args)
                                    function_response = {"result": result.content}
                                    print(f"✅ Tool call successful")
                                except Exception as e:
                                    function_response = {"error": str(e)}
                                    print(f"❌ Tool call failed: {str(e)}")

                                # Create function response content
                                function_response_part = types.Part.from_function_response(
                                    name=function_call_part.function_call.name,
                                    response=function_response
                                )
                                function_response_content = types.Content(
                                    role='tool',
                                    parts=[function_response_part]
                                )
                                
                                # Add both function call and response to conversation
                                conversation_contents.append(function_call_part)
                                conversation_contents.append(function_response_content)
                                
                            else:
                                # This is text content, not a function call
                                if part.text:
                                    final_text.append(part.text)
            
            # If no function call was made, break the loop
            if not has_function_call:
                print(f"✅ No more tool calls needed. Finalizing response...")
                break
            else:
                print(f"🔄 Tool call completed, checking if more are needed...")
        
        # If we reached max iterations, get the final response
        if iteration >= max_iterations:
            print(f"⚠️  Reached maximum iterations ({max_iterations}), getting final response...")
            final_response = self.genai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=conversation_contents,
                config=types.GenerateContentConfig(
                    tools=self.function_declarations,
                ),
            )
            
            final_text = []
            for candidate in final_response.candidates:
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        if isinstance(part, types.Part) and part.text:
                            final_text.append(part.text)
        
        final_response = "\n".join(final_text)
        
        # Add to conversation history
        self.add_to_history(query, final_response)
        
        generator = self.pipeline(final_response, voice='bm_george')

        # Process and save the generated audio segments
        for i, (gs, ps, audio) in enumerate(generator):
            print(f"🎵 Segment {i}: {gs}, {ps}")
            filename = f'output_{i}.wav'
            sf.write(filename, audio, 24000)
            print(f"💾 Saved audio segment to {filename}")
        
        return final_response

    async def cleanup(self):
        await self.exit_stack.aclose()

def clean_schema(schema):
    if isinstance(schema, dict):
        if 'oneOf' in schema and isinstance(schema.get('oneOf'), list) and schema['oneOf']:
            return clean_schema(schema['oneOf'][0])
        schema.pop("title", None)
        schema.pop("$ref", None)
        schema.pop("$defs", None)
        if "properties" in schema and isinstance(schema["properties"], dict):
            for key in schema["properties"]:
                schema["properties"][key] = clean_schema(schema["properties"][key])
    return schema

def convert_mcp_tools_to_gemini(mcp_tools):
    gemini_tools = []
    for tool in mcp_tools:
        parameters = clean_schema(tool.inputSchema)
        function_declaration = FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters=parameters
        )
        gemini_tool = Tool(function_declarations=[function_declaration])
        gemini_tools.append(gemini_tool)
    return gemini_tools

# async def main():
#     # if len(sys.argv) < 2:
#     #     print("Usage: python client.py <path_to_server_script>")
#     #     sys.exit(1)
    
#     # You can adjust the history length here
#     history_length = 5  # Keep last 5 interactions
#     client = MCPClient(history_length=history_length)
#     try:
#         await client.connect_to_servers()
#         # await client.connect_to_tcp_server()
#         # await client.connect_to_server(sys.argv[1])
#         await client.send_query("What is the weather like today?")
#     finally:
#         await client.cleanup()

