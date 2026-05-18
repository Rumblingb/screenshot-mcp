"""
Screenshot MCP Server
=====================
Provides tools to capture webpage screenshots via the ScreenshotOne API.
Free tier: 100 screenshots/month. Paid: $19/mo for 2,000 screenshots.
"""

import os
import base64
import httpx
from typing import Optional
from mcp.server.lowlevel import Server, Notification
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent, ImageContent, CallToolResult
from pydantic import BaseModel, Field

# ── Configuration ─────────────────────────────────────────────────────────────
API_KEY = os.environ.get("SCREENSHOTONE_API_KEY", "")
API_URL = "https://api.screenshotone.com/take"
STRIPE_LINK = "https://buy.stripe.com/dRm6oJ4Hd2Jugek0wz1oI0m"

# ── Server instance ───────────────────────────────────────────────────────────
server = Server("screenshot-mcp")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check_api_key() -> str | None:
    """Return an error message if the API key is missing, else None."""
    if not API_KEY:
        instructions = (
            "⚠️  ScreenshotOne API key not configured.\n\n"
            "To use this server, set the SCREENSHOTONE_API_KEY environment variable.\n\n"
            "1. Get a free API key at: https://screenshotone.com\n"
            "2. For production: $19/mo (2,000 screenshots)\n"
            "   Subscribe here: " + STRIPE_LINK + "\n\n"
            "3. Test the API with cURL:\n\n"
            "   curl -o screenshot.png \"" + API_URL + "?url=https://example.com"
            "&access_key=YOUR_API_KEY&viewport_width=1280&viewport_height=720\"\n\n"
            "4. Then restart this server with:\n"
            "   export SCREENSHOTONE_API_KEY=your_key_here\n"
            "   uv run server.py"
        )
        return instructions
    return None


def _build_params(
    url: str,
    width: int = 1280,
    height: int = 720,
    selector: str | None = None,
) -> dict:
    """Build query parameters for the ScreenshotOne API."""
    params = {
        "access_key": API_KEY,
        "url": url,
        "viewport_width": width,
        "viewport_height": height,
        "full_page": "false",
        "format": "png",
        "image_quality": 80,
        "block_ads": "true",
        "block_cookie_banners": "true",
        "block_trackers": "true",
        "delay": 2,
        "scroll_to_bottom": "false",
    }
    if selector:
        params["selector"] = selector
    return params


async def _take_screenshot(params: dict) -> bytes:
    """Call ScreenshotOne API and return raw PNG bytes."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(API_URL, params=params)
        resp.raise_for_status()
        return resp.content


def _png_to_base64(png_bytes: bytes) -> str:
    """Encode raw PNG bytes to a base64 string."""
    return base64.b64encode(png_bytes).decode("utf-8")


def _error_result(message: str) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=message)],
        isError=True,
    )


def _image_result(b64: str, alt: str) -> CallToolResult:
    return CallToolResult(
        content=[
            ImageContent(
                type="image",
                data=b64,
                mimeType="image/png",
                alt=alt,
            )
        ]
    )


# ── Tool implementations ──────────────────────────────────────────────────────

async def _screenshot_url(
    url: str,
    width: int = 1280,
    height: int = 720,
) -> CallToolResult:
    """Take a full-page screenshot of a URL at desktop viewport size."""
    # Check API key first
    missing = _check_api_key()
    if missing:
        return _error_result(missing)

    # Validate URL
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    params = _build_params(url, width=width, height=height)
    try:
        png = await _take_screenshot(params)
        b64 = _png_to_base64(png)
        return _image_result(b64, f"Screenshot of {url}")
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.text[:500]
        except Exception:
            detail = str(e)
        return _error_result(f"ScreenshotOne API error ({e.response.status_code}): {detail}")
    except Exception as e:
        return _error_result(f"Failed to take screenshot: {e}")


async def _screenshot_url_mobile(url: str) -> CallToolResult:
    """Take a screenshot at iPhone 13 Pro viewport (390×844)."""
    missing = _check_api_key()
    if missing:
        return _error_result(missing)

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    params = _build_params(url, width=390, height=844)
    try:
        png = await _take_screenshot(params)
        b64 = _png_to_base64(png)
        return _image_result(b64, f"Mobile screenshot of {url}")
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.text[:500]
        except Exception:
            detail = str(e)
        return _error_result(f"ScreenshotOne API error ({e.response.status_code}): {detail}")
    except Exception as e:
        return _error_result(f"Failed to take mobile screenshot: {e}")


async def _screenshot_element(
    url: str,
    selector: str,
) -> CallToolResult:
    """Screenshot a specific CSS selector element on the page."""
    missing = _check_api_key()
    if missing:
        return _error_result(missing)

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    params = _build_params(url, selector=selector)
    try:
        png = await _take_screenshot(params)
        b64 = _png_to_base64(png)
        return _image_result(b64, f"Element '{selector}' screenshot of {url}")
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.text[:500]
        except Exception:
            detail = str(e)
        return _error_result(f"ScreenshotOne API error ({e.response.status_code}): {detail}")
    except Exception as e:
        return _error_result(f"Failed to take element screenshot: {e}")


# ── MCP handlers ──────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="screenshot_url",
            description=(
                "Take a screenshot of a webpage at desktop viewport size "
                "(default 1280×720). Returns a PNG image. "
                "Free via ScreenshotOne API (100/mo) — set SCREENSHOTONE_API_KEY."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The webpage URL to screenshot",
                    },
                    "width": {
                        "type": "integer",
                        "description": "Viewport width in pixels (default: 1280)",
                        "default": 1280,
                    },
                    "height": {
                        "type": "integer",
                        "description": "Viewport height in pixels (default: 720)",
                        "default": 720,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="screenshot_url_mobile",
            description=(
                "Take a screenshot of a webpage at mobile viewport size "
                "(390×844, iPhone 13 Pro). Returns a PNG image. "
                "Free via ScreenshotOne API (100/mo) — set SCREENSHOTONE_API_KEY."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The webpage URL to screenshot",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="screenshot_element",
            description=(
                "Take a screenshot of a specific element on a webpage, identified "
                "by a CSS selector. Returns a PNG image. "
                "Free via ScreenshotOne API (100/mo) — set SCREENSHOTONE_API_KEY."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The webpage URL to screenshot",
                    },
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for the element to capture (e.g. '#main', '.hero', 'img.logo')",
                    },
                },
                "required": ["url", "selector"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str,
    arguments: dict,
) -> CallToolResult:
    if name == "screenshot_url":
        return await _screenshot_url(
            url=arguments["url"],
            width=arguments.get("width", 1280),
            height=arguments.get("height", 720),
        )
    elif name == "screenshot_url_mobile":
        return await _screenshot_url_mobile(url=arguments["url"])
    elif name == "screenshot_element":
        return await _screenshot_element(
            url=arguments["url"],
            selector=arguments["selector"],
        )
    else:
        return _error_result(f"Unknown tool: {name}")


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    async with server.run() as running:
        await running


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
