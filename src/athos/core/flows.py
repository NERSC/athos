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
    OpenAIServerModel, 
    Tool,
    # ToolCollection,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
        self.conversation_history: List[Dict[str, str]] = []
    
    async def execute(self, input_data: str) -> str:
        """Execute the flow"""
        return await self.process_message(input_data)
    
    async def process_message(self, message: str) -> str:
        """Process a single message through the chatbot"""
        user_message = {"role": "user", "content": message}
        self.conversation_history.append(user_message)
        
        # Add system prompt if provided
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        messages.extend(self.conversation_history)
        
        # response = await self.model.async_invoke(messages)
        response = self.model(messages, stop_sequences=["END"])
        assistant_message = {"role": "assistant", "content": response}
        self.conversation_history.append(assistant_message)
        
        return response

class CodeAgentFlow(BaseFlow):
    """Code agent flow with tools"""
    
    def __init__(self, model: OpenAIServerModel, tools: List[Tool]):
        self.agent = CodeAgent(
            tools=tools,
            model=model,
            # system_prompt=system_prompt
        )
    
    async def execute(self, input_data: str) -> str:
        """Execute the flow with input data"""
        return await self.execute_task(input_data)

    async def execute_task(self, task: str) -> str:
        """Execute a task using the code agent"""
        try:
            result = await self.agent.run(task)
            return result
        except Exception as e:
            logger.error(f"Code agent execution failed: {e}")
            return f"Error: {str(e)}"

# class PromptChainFlow(BaseFlow):
#     """Prompt chain flow for complex multi-step operations"""
    
#     def __init__(self, model: HfApiModel, prompt_chain: List[Dict[str, str]]):
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