import json
import subprocess
import sys
from pathlib import Path


def _decode_frame(output: bytes) -> dict:
    header, _, body = output.partition(b"\r\n\r\n")
    if not body:
        raise RuntimeError("No response frame received")

    header_text = header.decode("utf-8")
    content_length = None
    for line in header_text.split("\r\n"):
        if line.startswith("Content-Length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break

    if content_length is None:
        raise RuntimeError("Missing Content-Length header")

    return json.loads(body[:content_length].decode("utf-8"))


def _send_message(payload: dict) -> dict:
    proc = subprocess.Popen(
        [sys.executable, str(Path(__file__).with_name("app.py"))],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    body = json.dumps(payload).encode("utf-8")
    frame = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body
    stdout, stderr = proc.communicate(input=frame, timeout=5)
    assert proc.returncode == 0, stderr.decode("utf-8")
    return _decode_frame(stdout)


def test_initialize() -> None:
    response = _send_message(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert response["result"]["serverInfo"]["name"] == "mcp-server-app"


def test_tool_call() -> None:
    response = _send_message({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "echo", "arguments": {"message": "hello"}},
    })
    assert "hello" in response["result"]["content"][0]["text"]


def test_health_tool() -> None:
    response = _send_message({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "health", "arguments": {}},
    })
    assert "ok" in response["result"]["content"][0]["text"]
