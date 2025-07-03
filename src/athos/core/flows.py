# TODOs:
# - consider splitting flows into different modules, e.g. in new flows folder
# - create a Flow base class and consolidate the method names

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging
from smolagents import (
    CodeAgent,
    ToolCallingAgent,
    OpenAIServerModel,
    ChatMessage,
    Tool,
)

logger = logging.getLogger(__name__)


class BaseFlow(ABC):
    """Base class for all agent execution flows"""
    
    @abstractmethod
    async def execute(self, input_data: str) -> Any:
        """Execute the flow with input data"""
        pass

class ChatbotFlow(BaseFlow):
    """Simple chatbot flow without tools; maintains conv history"""

    def __init__(self, model: OpenAIServerModel, system_prompt: Optional[str] = None):
        self.model = model
        self.system_prompt = system_prompt
        self.conversation_history: List[ChatMessage] = []

    async def execute(self, input_data: str) -> str:
        """Execute the flow"""
        return await self.process_message(input_data)

    async def process_message(self, message: str) -> str:
        """Process a single message through the chatbot"""
        user_message = ChatMessage(role="user", content=message)
        self.conversation_history.append(user_message)
        
        try:
            # Add system prompt if provided
            messages = []
            if self.system_prompt:
                messages.append(ChatMessage(role="system",
                                            content=self.system_prompt))
            
            # Build input from full conversation history
            messages.extend(self.conversation_history)
            
            response = self.model(messages, stop_sequences=["END"])
            assistant_message = ChatMessage(role="assistant", content=response.content)
            self.conversation_history.append(assistant_message)
            
            return assistant_message.content
            
        except Exception as e:
            logger.error(f"Chatbot execution failed: {e}")
            model_config = dict(
                model_id=self.model.model_id,
                base_url=self.model.client_kwargs.get("base_url", "<not set>"),
                api_key=self.model.client_kwargs.get("api_key", "nul")[:3] + "..."
            )
            logger.error(f"Please check your model/API settings: {model_config}")
            error_response = f"Error: {str(e)}"
            
            # Add error response to conversation history to maintain context
            error_message = ChatMessage(role="assistant", content=error_response)
            self.conversation_history.append(error_message)
            
            return error_response



# class PromptChainFlow(BaseFlow):
#     """Prompt chain flow for complex multi-step operations"""
    
#     def __init__(self, model: HfApiModel, prompt_chain: List[Dict[str, str]]):
class AgentFlow(BaseFlow):
    """General agent flow supporting multiple agent types."""

    def __init__(self, model: OpenAIServerModel, tools: List[Tool], agent_type: str = "code"):
        if agent_type == "tool_calling":
            self.agent = ToolCallingAgent(tools=tools, model=model)
            self.agent_type = agent_type
        else:
            self.agent = CodeAgent(tools=tools, model=model)
            self.agent_type = "code"

    async def execute(self, input_data: str) -> Any:
        """Execute the flow with input data using the configured agent."""
        try:
            result = await asyncio.to_thread(self.agent.run, input_data)
            return result
        except Exception as e:
            logger.error(f"{self.agent.__class__.__name__} execution failed: {e}")
            model_config = dict(
                model_id=self.agent.model.model_id,
                base_url=self.agent.model.client_kwargs.get("base_url", "<not set>"),
                api_key=self.agent.model.client_kwargs.get("api_key", "nul")[:3] + "...",
            )
            logger.error(f"Please check your model/API settings: {model_config}")
            return f"Error: {str(e)}"

#         self.model = model
#         self.prompt_chain = prompt_chain
    
#     async def execute(self, input_data: str) -> Dict[str, str]:
#         """Execute the flow with input data"""
#         return await self.execute_chain(input_data)

#     async def execute_chain(self, initial_input: str) -> Dict[str, str]:
#         """Execute the entire prompt chain"""
#         results = {"initial_input": initial_input}
#         current_input = initial_input
        
#         for step in self.prompt_chain:
#             step_name = step["name"]
#             prompt_template = step["prompt"]
            
#             # Format prompt with previous results
#             formatted_prompt = prompt_template.format(**results, current_input=current_input)
            
#             # Execute step
#             response = await self.model.async_invoke([UserMessage(content=formatted_prompt)])
#             results[step_name] = response
#             current_input = response
            
#             logger.info(f"Completed step: {step_name}")
        
#         return results
