from typing import Optional, List

import openai
import agents as oai_agents

from athos.core.agent import Agent
from athos.core.tool import Tool


class OpenAIModelAgent(Agent):
    """
    A simple model wrapper for OpenAI API which doesn't leverage tools.

    This agent provides a basic interface to OpenAI's chat completion API
    without any tool calling or advanced agent capabilities. It's designed
    for straightforward text generation and conversation tasks.

    Attributes:
        client (openai.OpenAI): The OpenAI client instance
        model (str): The model name to use for completions
    """

    def __init__(self, api_key=None, base_url=None, model="gpt-3.5-turbo"):
        """
        Initialize the OpenAI model agent.

        Args:
            api_key (str, optional): OpenAI API key. If None, will use environment variable.
            base_url (str, optional): Custom base URL for OpenAI API.
            model (str): The model name to use. Defaults to "gpt-3.5-turbo".
        """
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.model = model   

    def chat_completion(self, messages, **kwargs):
        """
        Make a chat completion request to OpenAI API.

        Args:
            messages (list): List of message dictionaries with 'role' and 'content' keys.
            **kwargs: Additional parameters to pass to the OpenAI API.

        Returns:
            openai.types.chat.ChatCompletion: The completion response from OpenAI.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return response

    def generate_response(self, prompt, **kwargs):
        """
        Generate a response from a simple prompt.

        Args:
            prompt (str): The user prompt to generate a response for.
            **kwargs: Additional parameters to pass to the OpenAI API.

        Returns:
            str: The generated response content.
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.chat_completion(messages, **kwargs)
        return response.choices[0].message.content.strip()

    def run(self, prompt, **kwargs):
        """
        Run the agent with a given prompt.

        This is the main entry point for the agent, providing a simple
        interface for generating responses.

        Args:
            prompt (str): The user prompt to process.
            **kwargs: Additional parameters to pass to the OpenAI API.

        Returns:
            str: The generated response content.
        """
        return self.generate_response(prompt, **kwargs)


class OpenAITool(Tool):
    """
    A skeleton OpenAI tool implementation.
    """

    def __init__(self):
        super().__init__()

    def forward(self, *args, **kwargs) -> str:
        """
        Execute the tool.
        """
        return "Tool executed successfully"


class OpenAIAgent(Agent):
    """Wraps the OpenAI Agents SDK"""

    def __init__(
        self,
        name: str,
        instructions: str,
        tools: Optional[List[OpenAITool]] = None,
        model: str = "gpt-4",
        **kwargs
    ):
        super().__init__()
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools = tools or []

        self.agent = oai_agents.Agent(
            name=name,
            instructions=instructions,
            tools=[],
            model=model,
            **kwargs
        )
    
    def run(self, input_text: str, **kwargs) -> str:
        """Run the agent synchronously and return the final output."""
        result = oai_agents.Runner.run_sync(self._agent, input_text, **kwargs)
        return result.final_output