import os
import sys
import logging
from typing import Optional, List, Any
from pathlib import Path
from dotenv import load_dotenv

# Add the athos package to the Python path when run directly
if __name__ == "__main__":
    # Get the path to the athos package
    current_file = Path(__file__)
    athos_src_path = current_file.parent.parent.parent  # Go up to src directory
    sys.path.insert(0, str(athos_src_path))

from athos.core.agent import Agent
from athos.tools.slurm_query import query_jobs

# Import smolagents components
try:
    from smolagents import OpenAIServerModel, CodeAgent, ToolCollection, Tool, ToolCallingAgent
    from mcp import StdioServerParameters
    SMOLAGENTS_AVAILABLE = True
except ImportError:
    SMOLAGENTS_AVAILABLE = False
    logging.warning("smolagents not available. Install with: pip install smolagents")

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class HPCSmolAgent(Agent):
    """
    HPC Agent that integrates smolagents with MCP tools for SLURM, ServiceNow, and RAG capabilities.
    
    This agent provides a comprehensive interface for HPC operations including:
    - SLURM job management and monitoring
    - ServiceNow incident management (when configured)
    - RAG-based knowledge retrieval (when configured)
    - CBORG model integration for code generation
    """
    
    def __init__(
        self,
        model_id: str = "lbl/cborg-coder:latest",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        enable_slurm: bool = True,
        enable_servicenow: bool = False,
        enable_rag: bool = False,
        **kwargs
    ):
        """
        Initialize the HPC SmolAgent.
        
        Args:
            model_id: CBORG model identifier
            api_key: CBORG API key (defaults to environment variable)
            api_base: CBORG API URL (defaults to environment variable ``CBORG_API_URL``)
            enable_slurm: Whether to enable SLURM MCP tools
            enable_servicenow: Whether to enable ServiceNow MCP tools
            enable_rag: Whether to enable RAG MCP tools
        """
        super().__init__()
        
        if not SMOLAGENTS_AVAILABLE:
            raise ImportError("smolagents is required. Install with: pip install smolagents")
        
        # Initialize model
        self.model_id = model_id
        self.api_key = api_key or os.getenv("CBORG_API_KEY")
        self.api_base = api_base or os.getenv("CBORG_API_URL")
        
        if not self.api_key or not self.api_base:
            raise ValueError("CBORG_API_KEY and CBORG_API_URL must be set")
        
        self.model = OpenAIServerModel(
            model_id=model_id,
            api_key=self.api_key,
            api_base=self.api_base
        )
        
        # Tool configuration
        self.enable_slurm = enable_slurm
        self.enable_servicenow = enable_servicenow
        self.enable_rag = enable_rag
        
        # Initialize tools and keep MCP connections alive
        self.tools = []
        self.tool_collections = []  # Keep references to prevent context manager cleanup
        self._setup_tools()
        
        # Initialize agent
        self.agent = CodeAgent(
            tools=self.tools,
            model=self.model,
            add_base_tools=False,
            additional_authorized_imports=["json", "re", "subprocess", "os"]
        )
    
    def _setup_tools(self):
        """Set up MCP tools based on configuration."""
        # Get the athos tools directory path
        try:
            import athos.tools
            athos_tools_path = Path(athos.tools.__path__[0])
            logger.info(f"Using athos.tools path: {athos_tools_path}")
        except (ImportError, AttributeError):
            # Fallback: calculate path relative to this file
            current_file = Path(__file__)
            athos_tools_path = current_file.parent.parent / "tools"
            logger.info(f"Using fallback path: {athos_tools_path}")
        
        # SLURM tools
        if self.enable_slurm:
            try:
                slurm_path = athos_tools_path / "slurm_mcp"
                logger.info(f"SLURM MCP path: {slurm_path}")
                logger.info(f"SLURM MCP path exists: {slurm_path.exists()}")
                
                slurm_parameters = StdioServerParameters(
                    command="uv",
                    args=["run", "python", "slurm_mcp_server.py"],
                    env={},
                    cwd=str(slurm_path)
                )
                
                # Create tool collection and enter the context manager
                slurm_context = ToolCollection.from_mcp(slurm_parameters, trust_remote_code=True)
                slurm_tools = slurm_context.__enter__()
                self.tools.extend(slurm_tools.tools)
                self.tool_collections.append(slurm_context)
                logger.info(f"Loaded {len(slurm_tools.tools)} SLURM tools")
            except Exception as e:
                logger.error(f"Failed to load SLURM tools: {e}")
        
        # ServiceNow tools
        if self.enable_servicenow:
            try:
                import athos.tools.servicenow_mcp as servicenow_pkg
                servicenow_path = Path(servicenow_pkg.__path__[0])
                logger.info(f"ServiceNow MCP path: {servicenow_path}")
                logger.info(f"ServiceNow MCP path exists: {servicenow_path.exists()}")

                servicenow_parameters = StdioServerParameters(
                    command="uv",
                    args=["run", "python", "-m", "athos.tools.servicenow_mcp.cli"],
                    env={
                        "SERVICENOW_INSTANCE_URL": os.getenv("SERVICENOW_INSTANCE_URL"),
                        "SERVICENOW_USERNAME": os.getenv("SERVICENOW_USERNAME"),
                        "SERVICENOW_PASSWORD": os.getenv("SERVICENOW_PASSWORD"),
                        "SERVICENOW_AUTH_TYPE": os.getenv("SERVICENOW_AUTH_TYPE")
                    },
                    cwd=str(servicenow_path)
                )
                
                # Create tool collection and enter the context manager
                sn_context = ToolCollection.from_mcp(servicenow_parameters, trust_remote_code=True)
                sn_tools = sn_context.__enter__()
                self.tools.extend(sn_tools.tools)
                self.tool_collections.append(sn_context)
                logger.info(f"Loaded {len(sn_tools.tools)} ServiceNow tools")
            except Exception as e:
                logger.error(f"Failed to load ServiceNow tools: {e}")
        
        # RAG tools (commented out in original smol.py)
        if self.enable_rag:
            try:
                rag_parameters = StdioServerParameters(
                    command="rag-mcp",
                    env={},
                )
                
                # Create tool collection and enter the context manager
                rag_context = ToolCollection.from_mcp(rag_parameters, trust_remote_code=True)
                rag_tools = rag_context.__enter__()
                self.tools.extend(rag_tools.tools)
                self.tool_collections.append(rag_context)
                logger.info(f"Loaded {len(rag_tools.tools)} RAG tools")
            except Exception as e:
                logger.error(f"Failed to load RAG tools: {e}")
        
        # Log all available tools
        logger.info(f"Total tools loaded: {len(self.tools)}")
        logger.info("Available tools:")
        for tool in self.tools:
            logger.info(f"  - {tool.name}: {tool.description}")
    
    def run(self, prompt: str, **kwargs) -> Any:
        """
        Run the agent with the given prompt.
        
        Args:
            prompt: The user prompt/task to execute
            **kwargs: Additional arguments for the agent
            
        Returns:
            The agent's response/result
        """
        try:
            logger.info(f"Running agent with prompt: {prompt[:100]}...")
            result = self.agent.run(prompt, **kwargs)
            logger.info("Agent completed successfully")
            return result
        except Exception as e:
            logger.error(f"Agent failed: {e}")
            raise
    
    def query_jobs(self, user: str = "demo") -> str:
        """
        Legacy method for backward compatibility.
        
        Args:
            user: Username to query jobs for
            
        Returns:
            Job information as string
        """
        return query_jobs(user)
    
    def get_available_tools(self) -> List[str]:
        """
        Get list of available tool names.
        
        Returns:
            List of tool names
        """
        return [tool.name for tool in self.tools]
    
    def close(self):
        """Explicitly close the agent and clean up resources."""
        try:
            self.cleanup()
            logger.info("Agent closed successfully")
        except Exception as e:
            logger.error(f"Error closing agent: {e}")
    
    def cleanup(self):
        """Clean up MCP connections."""
        try:
            for context in self.tool_collections:
                if hasattr(context, '__exit__'):
                    try:
                        # Try to exit gracefully without forcing event loop closure
                        context.__exit__(None, None, None)
                    except RuntimeError as e:
                        if "Cannot close a running event loop" in str(e):
                            # Log but don't fail - this is expected when event loop is running
                            logger.debug(f"Event loop cleanup skipped: {e}")
                        else:
                            # Re-raise other RuntimeErrors
                            raise
            self.tool_collections.clear()
            logger.info("MCP connections cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            # Ignore errors in destructor to avoid masking other issues
            pass
    
    def test_slurm_tools(self) -> str:
        """
        Test SLURM tools functionality.
        
        Returns:
            Test results
        """
        test_task = """
        Use the sacct tool to get basic job information. Try these commands:
        1. Get help information: sacct --help
        2. Get a summary of recent jobs: sacct -S today
        3. Show job details with specific format: sacct -S today --format=JobID,JobName,State,ExitCode,Start,End
        """
        return self.run(test_task)


# Convenience function for backward compatibility
def run_agent_with_tools():
    """Run the agent with all available tools."""
    agent = HPCSmolAgent(
        enable_slurm=True,
        enable_servicenow=False,  # Set to True if ServiceNow is configured
        enable_rag=False,         # Set to True if RAG is configured
    )
    
    tasks = [
        "Look up my disk usage and quota",
        "Show me recent SLURM jobs",
        "What's the current system status?"
    ]
    
    for i, task in enumerate(tasks, 1):
        logger.info(f"Running task {i}: {task}")
        try:
            result = agent.run(task)
            logger.info(f"Task {i} result: {result}")
        except Exception as e:
            logger.error(f"Task {i} failed: {e}")


if __name__ == "__main__":
    # Example usage
    agent = HPCSmolAgent(enable_servicenow=True, enable_slurm=False)
    try:
        result = agent.run("Look for tickets related to user steven farrell")
        print(result)
    finally:
        # Explicitly close the agent to clean up resources
        agent.close()
