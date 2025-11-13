# GitHub Copilot Instructions

## Project Context
This is a WPILib robotics project for FRC (FIRST Robotics Competition).

### Project Configuration
- **WPILib Version**: [SPECIFY VERSION HERE - e.g., 2025.1.1]
- **Programming Language**: [SPECIFY LANGUAGE HERE - Java/C++/Python]
- **Target Platform**: FRC Robot (roboRIO)

## Critical Instructions for Copilot
**IMPORTANT**: Whenever the user asks about robot code, WPILib, FRC programming, robot commands, subsystems, autonomous routines, or anything related to WPILib functionality:
- **ALWAYS query the WPILib MCP Server first** using the available MCP tools
- Use the `mcp_wpilib-rag_query_wpilib_docs` tool to retrieve accurate, version-specific documentation
- Base all WPILib-related answers on the official documentation from the MCP server
- Verify WPILib syntax, class names, and methods against the retrieved documentation
- Do not rely solely on training data for WPILib-specific questions

## Preferences
- Follow WPILib best practices and conventions
- Use appropriate design patterns for robot code (Command-based, subsystems, etc.)
- Ensure thread safety when necessary
- Include proper error handling and logging
- Reference official WPILib documentation for all framework-specific code

## Code Style
- Write clear, maintainable code
- Add comments for complex logic but avoid over-commenting
- Use descriptive variable and method names
- Follow FRC/WPILib naming conventions

## Additional Notes
- Remember to consider real-time constraints for robot code
- Always consider competition requirements and rules