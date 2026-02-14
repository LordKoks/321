"""MetaGPT tool for OpenHands."""

from typing import TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from openhands.sdk.conversation.state import ConversationState

from openhands.sdk.tool import (
    Action,
    Observation,
    ToolAnnotations,
    ToolDefinition,
    register_tool,
)


class MetaGPTAction(Action):
    """Schema for MetaGPT operations."""

    command: str = Field(description="Command to run, e.g., 'generate_repo'")
    idea: str = Field(description="Idea for the project")
    project_name: str | None = Field(default=None, description="Name of the project")


class MetaGPTObservation(Observation):
    """Observation for MetaGPT tool."""

    output: str = Field(description="Output from MetaGPT")


@register_tool
class MetaGPTTool(ToolDefinition):
    """Tool for running MetaGPT multi-agent workflows."""

    name: str = "meta_gpt"
    description: str = "Run MetaGPT to generate software projects using multi-agent workflows."
    annotations = ToolAnnotations(
        requires_confirmation=True,
        mutable=True,
    )

    def run(self, action: MetaGPTAction, state: "ConversationState") -> MetaGPTObservation:
        """Run the MetaGPT tool."""
        if action.command == "generate_repo":
            from metagpt.software_company import generate_repo
            # Run in asyncio
            import asyncio
            result = asyncio.run(generate_repo(action.idea, project_name=action.project_name or ""))
            return MetaGPTObservation(output=str(result))
        else:
            return MetaGPTObservation(output="Unknown command")