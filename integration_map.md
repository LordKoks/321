# Integration Map for MetaGPT + OpenHands + VS Code ACP Extension

## MetaGPT Core Files
- `/workspaces/321/metagpt/metagpt/software_company.py`: Main entry for software generation workflows.
- `/workspaces/321/metagpt/metagpt/roles/`: Directory with role definitions (e.g., Architect, Engineer).
- `/workspaces/321/metagpt/metagpt/actions/`: Actions for roles.
- `/workspaces/321/metagpt/metagpt/llm.py`: LLM interface.

## OpenHands Agent Server Files
- `/workspaces/321/openhands/openhands-agent-server/openhands/agent_server/__main__.py`: Main server entry.
- `/workspaces/321/openhands/openhands-agent-server/openhands/agent_server/tool_router.py`: Router for tools.
- `/workspaces/321/openhands/openhands-agent-server/openhands/agent_server/api.py`: API endpoints.
- `/workspaces/321/openhands/openhands-agent-server/openhands/agent_server/models.py`: Data models.

## VS Code ACP Extension Files
- `/workspaces/321/vscode-acp/package.json`: Extension manifest.
- `/workspaces/321/vscode-acp/src/extension.ts`: Main extension code.
- `/workspaces/321/vscode-acp/src/acp/`: ACP protocol implementation.

## Integration Points
- Add MetaGPT as dependency in OpenHands `pyproject.toml`.
- Create `MetaGPTTool` in OpenHands `tools/` directory, wrapping MetaGPT functions.
- Extend OpenHands Agent to support sub-roles from MetaGPT.
- Enable MCP in OpenHands for tool exposure.
- Modify ACP extension to detect and connect to hybrid OpenHands agent.
- Use VS Code AI APIs (vscode.lm) for chat integration.
- Ensure no conflicts with Copilot (separate UI elements).

## Progress
- Checkpoint 1: Repos cloned, map created.
- Sub-task 1: MetaGPT added to OpenHands dependencies.
- Sub-task 2: MetaGPTTool created in OpenHands tools.
- Sub-task 3: MCP support exists in OpenHands.
- Sub-task 4: OpenHands added to ACP agents in extension.
- Sub-task 5: VS Code API referenced, extension compiled and packaged.
- Changed Python versions to 3.11 for compatibility with MetaGPT.
- Issue: Dependency conflict with tenacity (MetaGPT uses 8.2.3, OpenHands SDK uses >=9.1.2). Docker build failed.
- Recommendation: Use separate environments for MetaGPT and OpenHands, integrate via API calls instead of direct import.

## Next Steps
Resolved dependency conflicts by updating tenacity in MetaGPT to >=9.1.2 and using local path. Docker build successful: Created unified image with MetaGPT and OpenHands integrated as one system. Ready for end-to-end testing: Run container, connect via VS Code extension, execute multi-agent tasks.

## Web Version and Executable
- Web Version: Use OpenHands example ui_with_chainlit for web UI. Modify to include MetaGPT tool. Run: `cd openhands/examples/ui_with_chainlit && chainlit run app.py` after installing dependencies.
- Full Executable: Extract binary from Docker: `docker cp openhands-agent:/app/openhands-agent-server ./agent-binary`. Run standalone.
- APK: Created mobile app in /workspaces/321/mobile-app. To build APK: Install Android SDK, then `npx cap build android`. The app connects to agent server for AI interactions.</content>
<parameter name="filePath">/workspaces/321/integration_map.md