# FRC-RAG-MCP-Server
This contains a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/docs/getting-started/intro) Server that provides RAG-based access to WPILib documentation for FRC robotics programming.

## ⚠️ IMPORTANT: Beta Status & Availability

**This service is currently in BETA and is hosted locally.** 

**The **ONLY** available version of WPILib that is currently supported is WPILib 2025.3.2 Release I will add 2026 as soon as it gets released.**

- **Limited Availability**: The server may experience downtime or interruptions
- **Performance**: Response times may vary based on network conditions
- **Scaling**: If demand increases, scaling infrastructure is already planned and ready to deploy
- **No SLA**: This is a community service provided as-is during the beta period

Please be patient as we work to improve reliability and performance. If you experience connectivity issues, please report them so we can address them.

---

## Benefits of This Setup

A bad practice of WPILib is the yearly breaking changes, while this was ok in the past, with the popularity of agentic coding it's become clear that something needs to be done to help mitigate this issue. This is why this project exists and provides:

✅ **Accurate Information**: Responses based on official WPILib documentation

✅ **Version-Specific**: Get answers for your specific WPILib version

✅ **Up-to-Date**: Documentation can be updated without retraining the AI

✅ **Context-Aware**: Copilot understands your project's FRC/WPILib context

## What is RAG?

**RAG (Retrieval-Augmented Generation)** is a technique that enhances AI responses by retrieving relevant information from a knowledge base before generating answers. Instead of relying solely on the AI's training data, RAG:

1. **Retrieves** relevant documentation chunks from a vector database based on your question
2. **Augments** the AI's context with this retrieved information
3. **Generates** accurate, up-to-date answers based on the official documentation

This ensures that whatever GenAI model you're using provides accurate, version-specific WPILib guidance rather than potentially outdated information from its training data.

## What is a Copilot Instructions File?

The **`.github/copilot-instructions.md`** file is a special configuration file that customizes how GitHub Copilot behaves in your project. It:

- **Guides Copilot's behavior** for your specific project context
- **Instructs when to use MCP tools** (e.g., "always query the WPILib MCP server for robot code questions")
- **Sets coding standards** and conventions for your team
- **Defines project-specific preferences** (framework versions, design patterns, etc.)

### Why It's Critical for This Project

For this WPILib RAG MCP server to work effectively, the Copilot instructions file **must explicitly tell Copilot to query the MCP server** for WPILib-related questions. Without this instruction, Copilot might rely on its training data instead of the accurate, up-to-date documentation in the MCP server.

## Setup Instructions

### 1. The MCP Server

The MCP server is already running at `http://97.139.150.106:3000`. You don't need to install or run anything - just configure VS Code to connect to it.

### 2. Configure VS Code to Connect to the MCP Server

You need to add the MCP server configuration to VS Code. There are two ways to do this:

#### Option A: Automatic Setup (Recommended)

Copy the provided `.vscode/mcp.json` file to your VS Code user configuration:

**Windows**:
```cmd
copy .vscode\mcp.json %APPDATA%\Code\User\mcp.json
```

**macOS/Linux**:
```bash
cp .vscode/mcp.json ~/.config/Code/User/mcp.json
```

#### Option B: Manual Configuration

1. Open VS Code's user configuration folder:
   - **Windows**: `%APPDATA%\Code\User\`
   - **macOS/Linux**: `~/.config/Code/User/`

2. Create or edit the file `mcp.json` in that folder

3. Add the following configuration:

```json
{
	"servers": {
		"WPILibRag": {
			"url": "http://97.139.150.106:3000/",
			"type": "http"
		}
	},
	"inputs": []
}
```

**Important Notes:**
- The server name must be exactly `WPILibRag` (case-sensitive)
- The URL includes the trailing slash
- This is an HTTP-based MCP server, not stdio-based
- The server is remotely hosted - no local installation needed

### 3. Create the Copilot Instructions File

Create a `.github` folder in your project root (if it doesn't exist), then create `copilot-instructions.md` inside it:

```
your-project/
├── .github/
│   └── copilot-instructions.md
├── src/
├── README.md
└── ... other files
```

### 4. Configure the Copilot Instructions File

Add the following content to `.github/copilot-instructions.md`:

```markdown
# GitHub Copilot Instructions

## Project Context
This is a WPILib robotics project for FRC (FIRST Robotics Competition).

### Project Configuration
- **WPILib Version**: 2025.1.1
- **Programming Language**: Java (or C++/Python)
- **Target Platform**: FRC Robot (roboRIO)

## Critical Instructions for Copilot
**IMPORTANT**: Whenever the user asks about robot code, WPILib, FRC programming, 
robot commands, subsystems, autonomous routines, or anything related to WPILib functionality:
- **ALWAYS query the WPILib MCP Server first** using the available MCP tools
- Use the `mcp_wpilibrag_query_wpilib_docs` tool from the WPILibRag server to retrieve accurate, version-specific documentation
- Base all WPILib-related answers on the official documentation from the MCP server
- Verify WPILib syntax, class names, and methods against the retrieved documentation
- Do not rely solely on training data for WPILib-specific questions

## Preferences
- Follow WPILib best practices and conventions
- Use command-based programming paradigm
- Implement proper subsystem organization
- Include error handling and logging
- Reference official WPILib documentation for all framework-specific code

## Code Style
- Write clear, maintainable code
- Add comments for complex logic
- Use descriptive variable and method names
- Follow FRC/WPILib naming conventions
```

### 5. Verify the Setup

1. **Restart VS Code** to ensure all configurations are loaded
2. Open GitHub Copilot Chat (Ctrl+Alt+I or Cmd+Alt+I)
3. Ask a WPILib question: "How do I create a drivetrain subsystem in WPILib?"
4. Copilot should query the MCP server and provide documentation-based answers

### 6. Testing MCP Server Connectivity

You can verify the MCP server is working by asking Copilot:

- "What's the latest WPILib version available?"
- "Show me how to use PIDController in WPILib"
- "What languages are available in the WPILib documentation?"

Copilot will use the MCP tools to query the documentation server.

## How It All Works Together

```
┌─────────────────┐
│   Your Code     │
│   Questions     │
└────────┬────────┘
         │
         v
┌─────────────────────────────────────┐
│   GitHub Copilot                    │
│   (reads copilot-instructions.md)   │
└────────┬────────────────────────────┘
         │
         v
┌─────────────────────────────────────┐
│   MCP Server                        │
│   (WPILibRag)                       │
└────────┬────────────────────────────┘
         │
         v
┌─────────────────────────────────────┐
│   RAG System                        │
│   - Vector Database                 │
│   - WPILib Documentation Chunks     │
│   - Similarity Search               │
└────────┬────────────────────────────┘
         │
         v
┌─────────────────────────────────────┐
│   Retrieved Documentation           │
│   (sent back to Copilot)            │
└─────────────────────────────────────┘
```

## Available MCP Tools

This MCP server provides the following tools:

- `mcp_wpilibrag_query_wpilib_docs` - Query WPILib documentation by version and language
- `mcp_wpilibrag_get_latest_version` - Get the latest WPILib version available
- `mcp_wpilibrag_list_available_versions` - List all available WPILib versions
- `mcp_wpilibrag_list_available_languages` - List available languages for a version
- `mcp_wpilibrag_embed_query` - Generate embedding vectors for custom searches

## Troubleshooting

### MCP Server Not Connecting
- Verify the `mcp.json` file is in the correct location (`%APPDATA%\Code\User\` on Windows)
- Check that the server name is exactly `WPILibRag` (case-sensitive)
- Ensure the URL is `http://97.139.150.106:3000/` with the trailing slash
- Restart VS Code after configuration changes
- Check the Output panel (View → Output → GitHub Copilot Chat)
- Verify you have internet connectivity to reach the remote server

### Copilot Not Using MCP Server
- Ensure `.github/copilot-instructions.md` exists in your project root
- Check that the instructions explicitly mention using the MCP server
- Try asking explicitly: "Query the WPILib MCP server for..."

### Outdated Documentation
- Check which WPILib version is loaded in the MCP server
- Update the version in your `copilot-instructions.md` to match
- Verify the RAG database has the correct version loaded



## Contributing
Still planning on what I am going to open-source and how much due to the running cost of this project. I will for sure open source something, but I may ask Vendors for a small fee to add their lib documentation to this. I hope that they join forces, instead of spin up their own versions of this.
