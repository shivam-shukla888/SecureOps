import logging
from app.adapters.base import BaseAgentAdapter
from app.adapters.http_adapter import GenericHTTPAgentAdapter
from app.adapters.simulated_adapter import SimulatedAgentAdapter
from app.schemas.agent import AgentResponse

logger = logging.getLogger(__name__)


from app.adapters.openai_adapter import OpenAICompatibleAgentAdapter


def get_agent_adapter(agent: AgentResponse) -> BaseAgentAdapter:
    provider = agent.provider.lower()
    if provider in ("openai", "openai_compatible", "groq", "vllm", "localai", "ollama", "mistral", "anthropic_compatible"):
        base_url = agent.endpoint_url.strip() if (agent.endpoint_url and agent.endpoint_url.strip()) else "https://api.openai.com/v1"
        logger.info(f"Instantiating OpenAICompatibleAgentAdapter for agent '{agent.agent_id}' at '{base_url}'")
        return OpenAICompatibleAgentAdapter(base_url=base_url)

    if agent.endpoint_url and agent.endpoint_url.strip():
        logger.info(f"Instantiating GenericHTTPAgentAdapter for agent '{agent.agent_id}' at '{agent.endpoint_url}'")
        return GenericHTTPAgentAdapter(endpoint_url=agent.endpoint_url)
    
    logger.info(f"Instantiating SimulatedAgentAdapter for agent '{agent.agent_id}' ({agent.name})")
    return SimulatedAgentAdapter(agent_name=agent.name)

