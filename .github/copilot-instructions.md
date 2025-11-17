# GitHub Copilot Instructions

⚠️ **CRITICAL - READ THIS FIRST** ⚠️
═══════════════════════════════════════════════════════════════════════════════

🛑 **MANDATORY REQUIREMENT - NO EXCEPTIONS** 🛑

Before answering ANY question about:
- WPILib APIs, classes, methods, or syntax
- Robot code (commands, subsystems, autonomous)
- FRC programming patterns or best practices
- Command-based programming
- Any WPILib framework functionality

YOU MUST:
1. **STOP** - Do not answer from memory or training data
2. **QUERY** - Use `mcp_wpilibrag_query_wpilib_docs` tool FIRST
3. **VERIFY** - Base your answer on the retrieved documentation
4. **CITE** - Reference the official WPILib documentation

This is NOT optional. This is a MANDATORY step for ALL WPILib-related questions.

═══════════════════════════════════════════════════════════════════════════════

## Project Context
This is a WPILib robotics project for FRC (FIRST Robotics Competition).

### Project Configuration
- **WPILib Version**: [SPECIFY VERSION HERE - e.g., 2025.1.1]
- **Programming Language**: [SPECIFY LANGUAGE HERE - Java/C++/Python]
- **Target Platform**: FRC Robot (roboRIO)

## WPILib RAG Server Usage
- **Tool Name**: `mcp_wpilibrag_query_wpilib_docs`
- **When to Use**: ALWAYS for any WPILib-related question (see mandatory requirement above)
- **Parameters**: 
  - `question`: The user's question
  - `version`: WPILib version (default: "2025")
  - `language`: "Java", "Python", "C++", or "API Reference"

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