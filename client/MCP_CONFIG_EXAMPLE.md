# MCP Server Configuration Examples

This document provides sample JSON configuration files for configuring the WPILib RAG MCP server with different MCP clients.

## Configuration Requirements

### Required Environment Variables

- **`VOYAGE_API_KEY`** (REQUIRED): Your Voyage AI API key for embedding generation
  - Get your API key at: https://www.voyageai.com/
  - This is required for the MCP server to generate embeddings for queries

### Optional Environment Variables

- **`CLOUD_DB_URL`**: Database download URL
  - Default: `http://97.139.150.106:3000/database/download`
  - Only set if you need to override the default database server URL

- **`WPILIB_RAG_AUTO_UPDATE`**: Enable automatic database updates
  - Set to `"true"` to automatically download database updates on startup
  - Default: `"true"` (auto-update is enabled by default)

- **`CHROMA_DB_PATH`**: Local path where database is stored
  - Default: Platform-specific user data directory
    - Windows: `%LOCALAPPDATA%\wpilib-rag\chroma_db`
    - macOS: `~/Library/Application Support/wpilib-rag/chroma_db`
    - Linux: `~/.local/share/wpilib-rag/chroma_db`

## VS Code Configuration

**Location**: VS Code Settings JSON (`File > Preferences > Settings > Open Settings JSON`)

```json
{
  "mcp": {
    "servers": {
      "wpilib-rag": {
        "command": "C:\\path\\to\\wpilib-rag-server\\wpilib-rag-server.exe",
        "env": {
          "VOYAGE_API_KEY": "your-voyage-api-key-here",
          "CLOUD_DB_URL": "http://97.139.150.106:3000/database/download",
          "WPILIB_RAG_AUTO_UPDATE": "true"
        }
      }
    }
  }
}
```

**macOS/Linux**: Update the command path to your executable:
```json
{
  "mcp": {
    "servers": {
      "wpilib-rag": {
        "command": "/path/to/wpilib-rag-server/wpilib-rag-server",
        "env": {
          "VOYAGE_API_KEY": "your-voyage-api-key-here",
          "CLOUD_DB_URL": "http://97.139.150.106:3000/database/download",
          "WPILIB_RAG_AUTO_UPDATE": "true"
        }
      }
    }
  }
}
```

## Claude Desktop Configuration

### Windows

**Location**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "wpilib-rag": {
      "command": "C:\\path\\to\\wpilib-rag-server\\wpilib-rag-server.exe",
      "env": {
        "VOYAGE_API_KEY": "your-voyage-api-key-here",
        "CLOUD_DB_URL": "http://97.139.150.106:3000/database/download",
        "WPILIB_RAG_AUTO_UPDATE": "false"
      }
    }
  }
}
```

### macOS

**Location**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "wpilib-rag": {
      "command": "/path/to/wpilib-rag-server/wpilib-rag-server",
      "env": {
        "VOYAGE_API_KEY": "your-voyage-api-key-here",
        "CLOUD_DB_URL": "http://97.139.150.106:3000/database/download",
        "WPILIB_RAG_AUTO_UPDATE": "false"
      }
    }
  }
}
```

### Linux

**Location**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "wpilib-rag": {
      "command": "/path/to/wpilib-rag-server/wpilib-rag-server",
      "env": {
        "VOYAGE_API_KEY": "your-voyage-api-key-here",
        "CLOUD_DB_URL": "http://97.139.150.106:3000/database/download",
        "WPILIB_RAG_AUTO_UPDATE": "false"
      }
    }
  }
}
```

## Development Configuration (using uv)

If running from source code using `uv`:

```json
{
  "mcpServers": {
    "wpilib-rag": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/wpilib-rag-mcpserver/client",
        "run",
        "wpilib-rag-server"
      ],
      "env": {
        "VOYAGE_API_KEY": "your-voyage-api-key-here",
        "CLOUD_DB_URL": "http://97.139.150.106:3000/database/download",
        "WPILIB_RAG_AUTO_UPDATE": "false"
      }
    }
  }
}
```

## Minimal Configuration

The minimal required configuration only needs the `VOYAGE_API_KEY`:

```json
{
  "mcpServers": {
    "wpilib-rag": {
      "command": "/path/to/wpilib-rag-server/wpilib-rag-server",
      "env": {
        "VOYAGE_API_KEY": "your-voyage-api-key-here"
      }
    }
  }
}
```

The database will automatically download from `http://97.139.150.106:3000/database/download` on first run.

## Notes

1. **API Key Security**: Never commit your `VOYAGE_API_KEY` to version control. Consider using environment variables or secure configuration management.

2. **Database Downloads**: The database is automatically downloaded on first run. No API key is required for database downloads - only for embedding generation.

3. **Auto-Update**: By default, `WPILIB_RAG_AUTO_UPDATE` is `"true"` in the code, so the database automatically updates on startup. The Claude Desktop examples show `"false"` to give users explicit control over when updates happen.

4. **Path Updates**: Make sure to update the `command` path to point to your actual executable location.

5. **Multiple Environments**: You can configure different settings for different environments by adjusting the environment variables in each configuration.
