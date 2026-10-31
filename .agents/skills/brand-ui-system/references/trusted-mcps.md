# Trusted MCPs

Use official/trusted MCPs by default.

## Figma MCP

Trusted source: official Figma MCP server.

Use the remote server when possible. Figma documents the hosted endpoint:

```text
https://mcp.figma.com/mcp
```

Generic MCP JSON:

```json
{
  "mcpServers": {
    "figma": {
      "type": "http",
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

Claude Code command:

```bash
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

Desktop fallback, only when remote is unavailable or the user needs local desktop workflows:

```text
http://127.0.0.1:3845/mcp
```

Claude Code desktop command:

```bash
claude mcp add --transport http figma-desktop http://127.0.0.1:3845/mcp
```

Desktop JSON:

```json
{
  "mcpServers": {
    "figma-desktop": {
      "type": "http",
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```

Notes:

- Prefer official Figma MCP over third-party Figma MCP packages.
- Figma remote MCP supports the broadest feature set according to Figma docs.
- Write-to-canvas and code-to-canvas features may depend on client support and Figma access.

## Storybook MCP

Trusted source: official Storybook MCP addon.

Install in a Storybook project:

```bash
npx storybook add @storybook/addon-mcp
```

Run Storybook, then connect the local MCP endpoint:

```text
http://localhost:6006/mcp
```

Configure with mcp-add:

```bash
npx mcp-add --type http --url "http://localhost:6006/mcp" --scope project
```

Generic MCP JSON:

```json
{
  "mcpServers": {
    "storybook": {
      "type": "http",
      "url": "http://localhost:6006/mcp"
    }
  }
}
```

Notes:

- Storybook docs currently describe MCP support as preview and primarily React-focused.
- Local Storybook MCP gives docs, development, and testing tools when configured.
- Use Storybook MCP to avoid hallucinating component props.

## Chromatic MCP

Trusted source: Chromatic, the Storybook maintainers' hosted platform.

Install the official Storybook MCP addon first:

```bash
npx storybook add @storybook/addon-mcp
```

Publish with Chromatic. The hosted MCP endpoint is the Storybook URL plus `/mcp`, for example:

```text
https://main--<appid>.chromatic.com/mcp
```

Chromatic setup command pattern:

```bash
npx mcp-add --type http --url "https://main--<appid>.chromatic.com/mcp" --client-id "cdf3737dff9d485485968e50b63fd8b4" --scope project
```

Generic MCP JSON:

```json
{
  "mcpServers": {
    "chromatic-storybook": {
      "type": "http",
      "url": "https://main--<appid>.chromatic.com/mcp"
    }
  }
}
```

Notes:

- Use Chromatic when the team needs remote/team access to Storybook MCP.
- Private Storybooks may require Chromatic authentication.

## Security Rule

Do not install third-party Figma MCP packages by default. If a user asks for one, verify source, maintenance, permissions, and known security advisories before recommending it.
