import json
import sys
from typing import Any, Dict, List, Optional

sys.dont_write_bytecode = True


class MCPServer:
    def __init__(self) -> None:
        self.server_info = {"name": "mcp-server-app", "version": "1.0.0"}
        self.tools: List[Dict[str, Any]] = [
            {
                "name": "echo",
                "description": "Return the provided text.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                    "required": ["message"],
                },
            },
            {
                "name": "health",
                "description": "Return a simple health payload.",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    def handle_message(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(payload, dict):
            return {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}}

        if payload.get("jsonrpc") != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": payload.get("id"),
                "error": {"code": -32600, "message": "Invalid Request"},
            }

        method = payload.get("method")
        params = payload.get("params") or {}
        request_id = payload.get("id")

        if method == "ping":
            return {"jsonrpc": "2.0", "id": request_id, "result": {"status": "pong"}}

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": self.server_info,
                },
            }

        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": self.tools}}

        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if tool_name == "echo":
                message = arguments.get("message", "")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": f"echo: {message}"}],
                        "isError": False,
                    },
                }
            if tool_name == "health":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps({"status": "ok"})}],
                        "isError": False,
                    },
                }
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
            }

        if method == "notifications/initialized":
            return None

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method '{method}' not found"},
        }

    def run(self) -> None:
        while True:
            message = self._read_message(sys.stdin.buffer)
            if message is None:
                break
            response = self.handle_message(message)
            if response is not None:
                self._write_message(response)

    def _read_message(self, stream) -> Optional[Dict[str, Any]]:
        header = b""
        while b"\r\n\r\n" not in header:
            chunk = stream.read(1)
            if not chunk:
                return None
            header += chunk

        header_text = header.decode("utf-8")
        content_length = None
        for line in header_text.split("\r\n"):
            if line.startswith("Content-Length:"):
                content_length = int(line.split(":", 1)[1].strip())
                break

        if content_length is None:
            raise ValueError("Missing Content-Length header")

        body = stream.read(content_length)
        if not body:
            return None
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}

    def _write_message(self, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
        sys.stdout.buffer.write(header + body)
        sys.stdout.buffer.flush()


def main() -> None:
    print("Starting MCP server", file=sys.stderr)
    MCPServer().run()


if __name__ == "__main__":
    main()
