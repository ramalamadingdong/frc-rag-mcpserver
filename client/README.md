# WPILib RAG - Client Side

This is the MCP (Model Context Protocol) server that runs on users' machines to provide WPILib documentation retrieval.

## What is this?

The WPILib RAG client is an MCP server that:
- Connects to Claude Desktop or other MCP clients
- Retrieves relevant WPILib documentation based on queries
- Filters by version and programming language
- Uses a local ChromaDB database plus external embeddings (no LLM calls from this package)

## Installation

### For End Users (This is the goal, but it's not ready yet)

1. Download the standalone executable for your platform from this project's GitHub Releases page
2. Configure your MCP client (e.g., Claude Desktop, VS Code) to use it

See `MCP_CONFIG_EXAMPLE.md` for detailed configuration instructions.

### For Development

```bash
cd client
uv sync
```

## Configuration

The client needs:
1. **Embedding access** (Voyage AI) for query embeddings
2. **Database access** (ChromaDB with WPILib documentation)

Key environment variables:

- `VOYAGE_API_KEY` (required): Voyage AI API key used for embedding generation  
- `CLOUD_DB_URL` (optional): URL to download the ChromaDB database archive  
  - Default: `http://97.139.150.106:3000/database/download`
- `WPILIB_RAG_AUTO_UPDATE` (optional): Automatically download database updates on startup  
  - `"true"` to auto-update (default in code)  
  - `"false"` for manual updates only
- `CHROMA_DB_PATH` (optional): Local path where the database is stored  
  - Defaults to a platform-specific user data directory when running as an executable, or `./chroma_db` when running from source

For full MCP configuration examples (VS Code, Claude Desktop, development via `uv`), see `MCP_CONFIG_EXAMPLE.md`.

## Running

### As MCP Server

Add to your MCP client configuration (e.g., `claude_desktop_config.json`):

**Using standalone executable (recommended for end users):**

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

**Using uv for development:**

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
        "CLOUD_DB_URL": "http://97.139.150.106:3000/database/download"
      }
    }
  }
}
```

For more OS-specific examples and minimal configs, refer to `MCP_CONFIG_EXAMPLE.md`.

### Testing Locally

```bash
cd client
uv run wpilib-rag-server
```

## Project Structure

```
client/
├── src/
│   └── wpilib_rag/
│       ├── __init__.py
│       ├── __main__.py         # Entry point
│       ├── server.py           # MCP server implementation
│       ├── config.py           # Configuration
│       ├── query_engine.py     # Query logic
│       ├── embedding_client.py # Embedding generation
│       └── database_loader.py  # Database download and updates
├── MCP_CONFIG_EXAMPLE.md       # MCP configuration examples
├── build_executable.py         # PyInstaller build script
├── pyproject.toml
└── README.md (this file)
```

## Development

### Building Standalone Executable

```bash
cd client
uv sync --extra dev
uv run build_executable.py
```

This creates a standalone executable in `dist/` that requires no Python installation.

## How It Works

1. **First Run**: Downloads the ChromaDB database from `CLOUD_DB_URL` (default `http://97.139.150.106:3000/database/download`) if it does not exist locally  
2. **Updates**: Checks for database updates on startup and optionally auto-updates when `WPILIB_RAG_AUTO_UPDATE=true`  
3. **Query Processing**: 
   - User asks a question in Claude (or another MCP client)
   - The client calls the `query_wpilib_docs` MCP tool with question, version, and language
   - The MCP server generates an embedding using Voyage AI
   - The MCP server searches the local ChromaDB database
   - It returns relevant documentation chunks for the LLM to answer with citations

4. **API Keys**: Only a Voyage AI key (`VOYAGE_API_KEY`) is required for embeddings; database downloads from `CLOUD_DB_URL` do **not** require any API key.

## Database Updates

The client automatically checks for database updates and can notify you, for example:

```bash
$ wpilib-rag-server
============================================================
Database update available!
  Current: 2025.3.2
  New:     2025.4.0
  To update: Run 'wpilib-rag-update'
============================================================
```

**Manual update:**

```bash
wpilib-rag-update
```

**Auto-update**:

```bash
export WPILIB_RAG_AUTO_UPDATE=true
```

When enabled, the database will be updated automatically on startup when a newer version is available.

## Architecture

```
USER'S MACHINE (Client Side)
┌────────────────────────────────────────┐
│                                        │
│  ┌─────────────────┐                  │
│  │  Claude Desktop │                  │
│  │  (or MCP client)│                  │
│  └────────┬────────┘                  │
│           │                            │
│           ▼                            │
│  ┌─────────────────┐                  │
│  │  MCP Server     │◀──── Uses Voyage AI
│  │  (this code)    │      for embeddings
│  └────────┬────────┘                  │
│           │                            │
│           ▼                            │
│  ┌─────────────────┐                  │
│  │  Local ChromaDB │ (downloaded once │
│  │  (database)     │  & auto-updated) │
│  └─────────────────┘                  │
│                                        │
└────────────────────────────────────────┘
```

## Troubleshooting

**Database not downloading:**
- Check that `CLOUD_DB_URL` is set correctly (or rely on the default `http://97.139.150.106:3000/database/download`)
- Verify the database endpoint is reachable (e.g., `curl http://97.139.150.106:3000/database/version`)

**Update check fails:**
- Verify the base URL derived from `CLOUD_DB_URL` is reachable
- Check network connectivity to the database server
- Manually trigger an update: `wpilib-rag-update`

**Embedding errors:**
- Verify `VOYAGE_API_KEY` is set and valid
- Check Voyage AI account status and usage limits

**No results:**
- Verify the database directory exists (see `CHROMA_DB_PATH`)
- Check the database version: `cat <CHROMA_DB_PATH>/.db_version`
- Try different version/language filters
- Confirm the question is relevant to WPILib documentation

