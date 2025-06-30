# aura_agent/agents.py

from agents import Agent, AgentOutputSchema
from agents.extensions.models.litellm_model import LitellmModel
from . import config
from .task import Reflection
from .agentic_layer import anamkore_tools

# MODIFIED: Instructions are now more direct and provide a clear example.
planner_agent = Agent(
    name="Anamkore-Planner",
    instructions=(
        "You are a pure tool-calling agent. Your SOLE purpose is to convert a "
        "human-readable 'Directive' into a single, precise, and valid tool call. "
        "Your response MUST be ONLY a single tool call and nothing else. "
        "For example, if the directive is 'Read the file foo.py', your response "
        "should be ONLY `read_file(path='foo.py')`."
    ),
    tools=anamkore_tools,
    model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
    tool_use_behavior="stop_on_first_tool",
)

synthesizer_agent = Agent(
    name="Anamkore-Synthesizer",
    instructions=(
        "You are the 'Synthesizer' module. You will receive a 'Directive' and the "
        "raw 'Planner Output' from a tool execution. Your job is to synthesize this "
        "into a coherent, human-readable summary. If the planner output indicates "
        "success, explain the result. If it shows an error, explain the error."
    ),
    tools=[],
    model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
)

reflector_agent = Agent(
    name="AURA-Reflector",
    instructions=(
        "You are the self-reflection module. Analyze the provided cognitive cycle trace. "
        "Your most important task is to compare the current cycle to the previous one. If the "
        "current cycle successfully resolves an error from the previous cycle, it is a "
        "**high-value 'Correction' (Score 5)**. Your output MUST be a JSON object "
        "matching the `Reflection` schema."
    ),
    tools=[],
    model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
    output_type=AgentOutputSchema(Reflection, strict_json_schema=True),
)