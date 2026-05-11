# Screenshot MCP Server

A Model Context Protocol (MCP) server that captures webpage screenshots using the [ScreenshotOne](https://screenshotone.com) API.

> **Free tier:** 100 screenshots/month (no credit card required)  
> **Paid:** $19/month for 2,000 screenshots — [Subscribe here](https://buy.stripe.com/dRm6oJ4Hd2Jugek0wz1oI0m)

## Tools

| Tool | Description |
|------|-------------|
| `screenshot_url(url, width?, height?)` | Screenshot a webpage at desktop viewport (default 1280×720). Returns a base64 PNG. |
| `screenshot_url_mobile(url)` | Screenshot a webpage at mobile viewport (390×844, iPhone 13 Pro). Returns a base64 PNG. |
| `screenshot_element(url, selector)` | Screenshot a specific element on the page by CSS selector. Returns a base64 PNG. |

## Quick Start

### 1. Get an API Key

Sign up at [screenshotone.com](https://screenshotone.com) — free tier gives you 100 screenshots/month.

### 2. Set the environment variable

```bash
export SCREENSHOTONE_API_KEY=your_key_here
```

### 3. Run with `uv`

```bash
uv run server.py
```

Or install dependencies and run directly:

```bash
pip install -r requirements.txt
python server.py
```

## Usage with Claude Desktop / MCP Client

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "screenshot": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/screenshot-mcp", "server.py"],
      "env": {
        "SCREENSHOTONE_API_KEY": "your_key_here"
      }
    }
  }
}
```

## Testing with cURL

If you don't have the MCP client set up, you can test the API directly:

```bash
curl -o screenshot.png \
  "https://api.screenshotone.com/take?url=https://example.com&access_key=YOUR_API_KEY&viewport_width=1280&viewport_height=720"
```

## Deployment

### Smithery

This server is configured for [Smithery](https://smithery.ai) deployment. See `smithery.yaml` for details.

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
ENV SCREENSHOTONE_API_KEY=""
CMD ["python", "server.py"]
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SCREENSHOTONE_API_KEY` | Yes | Your ScreenshotOne API key |

## Pricing

| Plan | Screenshots | Price | Link |
|------|-------------|-------|------|
| Free | 100/month | $0 | [screenshotone.com](https://screenshotone.com) |
| Pro | 2,000/month | $19/mo | [Subscribe](https://buy.stripe.com/dRm6oJ4Hd2Jugek0wz1oI0m) |
