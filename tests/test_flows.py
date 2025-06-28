import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from smolagents import OpenAIServerModel, ChatMessage, Tool
from athos.core.flows import BaseFlow, ChatbotFlow, CodeAgentFlow, ToolCallingAgentFlow


class TestBaseFlow:
    """Test the abstract BaseFlow class"""
    
    def test_base_flow_is_abstract(self):
        """Test that BaseFlow cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseFlow()
    
    def test_base_flow_requires_execute_implementation(self):
        """Test that subclasses must implement execute method"""
        class IncompleteFlow(BaseFlow):
            pass
        
        with pytest.raises(TypeError):
            IncompleteFlow()


class TestChatbotFlow:
    """Test the ChatbotFlow class"""
    
    @pytest.fixture
    def mock_model(self):
        """Create a mock OpenAI model"""
        model = Mock(spec=OpenAIServerModel)
        mock_response = Mock(spec=ChatMessage)
        mock_response.content = "Test response"
        model.return_value = mock_response
        return model
    
    @pytest.fixture
    def chatbot_flow(self, mock_model):
        """Create a ChatbotFlow instance"""
        return ChatbotFlow(model=mock_model, system_prompt="You are a helpful assistant")
    
    def test_chatbot_flow_initialization(self, mock_model):
        """Test ChatbotFlow initialization"""
        flow = ChatbotFlow(model=mock_model, system_prompt="Test prompt")
        assert flow.model == mock_model
        assert flow.system_prompt == "Test prompt"
        assert flow.conversation_history == []
    
    def test_chatbot_flow_initialization_without_system_prompt(self, mock_model):
        """Test ChatbotFlow initialization without system prompt"""
        flow = ChatbotFlow(model=mock_model)
        assert flow.model == mock_model
        assert flow.system_prompt is None
        assert flow.conversation_history == []
    
    @pytest.mark.asyncio
    async def test_execute_calls_process_message(self, chatbot_flow):
        """Test that execute method calls process_message"""
        with patch.object(chatbot_flow, 'process_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = "Test response"
            
            result = await chatbot_flow.execute("Test input")
            
            mock_process.assert_called_once_with("Test input")
            assert result == "Test response"
    
    @pytest.mark.asyncio
    async def test_process_message_with_system_prompt(self, chatbot_flow):
        """Test process_message with system prompt"""
        result = await chatbot_flow.process_message("Hello")
        
        # Check that conversation history is updated
        assert len(chatbot_flow.conversation_history) == 2
        assert chatbot_flow.conversation_history[0].role == "user"
        assert chatbot_flow.conversation_history[0].content == "Hello"
        assert chatbot_flow.conversation_history[1].role == "assistant"
        assert chatbot_flow.conversation_history[1].content == "Test response"
        
        # Check that model was called with system prompt
        call_args = chatbot_flow.model.call_args[0][0]
        assert len(call_args) == 2  # system + user message
        assert call_args[0].role == "system"
        assert call_args[0].content == "You are a helpful assistant"
        assert call_args[1].role == "user"
        assert call_args[1].content == "Hello"
        
        assert result == "Test response"
    
    @pytest.mark.asyncio
    async def test_process_message_without_system_prompt(self, mock_model):
        """Test process_message without system prompt"""
        flow = ChatbotFlow(model=mock_model)
        
        result = await flow.process_message("Hello")
        
        # Check that model was called without system prompt
        call_args = mock_model.call_args[0][0]
        assert len(call_args) == 1  # user message only
        assert call_args[0].role == "user"
        
        assert result == "Test response"
    
    @pytest.mark.asyncio
    async def test_conversation_history_persistence(self, chatbot_flow):
        """Test that conversation history persists across messages"""
        await chatbot_flow.process_message("First message")
        await chatbot_flow.process_message("Second message")
        
        assert len(chatbot_flow.conversation_history) == 4
        assert chatbot_flow.conversation_history[0].content == "First message"
        assert chatbot_flow.conversation_history[2].content == "Second message"


class TestCodeAgentFlow:
    """Test the CodeAgentFlow class"""
    
    @pytest.fixture
    def mock_model(self):
        """Create a mock OpenAI model"""
        return Mock(spec=OpenAIServerModel)
    
    @pytest.fixture
    def mock_tools(self):
        """Create mock tools"""
        return [Mock(spec=Tool), Mock(spec=Tool)]
    
    @pytest.fixture
    def code_agent_flow(self, mock_model, mock_tools):
        """Create a CodeAgentFlow instance"""
        with patch('athos.core.flows.CodeAgent') as mock_code_agent:
            flow = CodeAgentFlow(model=mock_model, tools=mock_tools)
            return flow
    
    def test_code_agent_flow_initialization(self, mock_model, mock_tools):
        """Test CodeAgentFlow initialization"""
        with patch('athos.core.flows.CodeAgent') as mock_code_agent:
            flow = CodeAgentFlow(model=mock_model, tools=mock_tools)
            
            mock_code_agent.assert_called_once_with(
                tools=mock_tools,
                model=mock_model
            )
    
    @pytest.mark.asyncio
    async def test_execute_success(self, code_agent_flow):
        """Test successful execution of CodeAgentFlow"""
        code_agent_flow.agent.run.return_value = "Code execution result"
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = "Code execution result"
            
            result = await code_agent_flow.execute("Write a function")
            
            mock_to_thread.assert_called_once_with(code_agent_flow.agent.run, "Write a function")
            assert result == "Code execution result"
    
    @pytest.mark.asyncio
    async def test_execute_failure(self, code_agent_flow):
        """Test CodeAgentFlow execution with error"""
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = Exception("Test error")
            
            result = await code_agent_flow.execute("Write a function")
            
            assert result == "Error: Test error"
    
    @pytest.mark.asyncio
    async def test_execute_logs_error(self, code_agent_flow, caplog):
        """Test that errors are logged"""
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = Exception("Test error")
            
            await code_agent_flow.execute("Write a function")
            
            assert "Code agent execution failed: Test error" in caplog.text


class TestToolCallingAgentFlow:
    """Test the ToolCallingAgentFlow class"""
    
    @pytest.fixture
    def mock_model(self):
        """Create a mock OpenAI model"""
        return Mock(spec=OpenAIServerModel)
    
    @pytest.fixture
    def mock_tools(self):
        """Create mock tools"""
        return [Mock(spec=Tool), Mock(spec=Tool)]
    
    @pytest.fixture
    def tool_calling_agent_flow(self, mock_model, mock_tools):
        """Create a ToolCallingAgentFlow instance"""
        with patch('athos.core.flows.ToolCallingAgent') as mock_tool_calling_agent:
            flow = ToolCallingAgentFlow(model=mock_model, tools=mock_tools)
            flow.agent = mock_tool_calling_agent.return_value
            return flow
    
    def test_tool_calling_agent_flow_initialization(self, mock_model, mock_tools):
        """Test ToolCallingAgentFlow initialization"""
        with patch('athos.core.flows.ToolCallingAgent') as mock_tool_calling_agent:
            flow = ToolCallingAgentFlow(model=mock_model, tools=mock_tools)
            
            mock_tool_calling_agent.assert_called_once_with(
                tools=mock_tools,
                model=mock_model
            )
    
    @pytest.mark.asyncio
    async def test_execute_success(self, tool_calling_agent_flow):
        """Test successful execution of ToolCallingAgentFlow"""
        tool_calling_agent_flow.agent.run.return_value = "Tool calling result"
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = "Tool calling result"
            
            result = await tool_calling_agent_flow.execute("Use tools to solve this")
            
            mock_to_thread.assert_called_once_with(tool_calling_agent_flow.agent.run, "Use tools to solve this")
            assert result == "Tool calling result"
    
    @pytest.mark.asyncio
    async def test_execute_failure(self, tool_calling_agent_flow):
        """Test ToolCallingAgentFlow execution with error"""
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = Exception("Tool error")
            
            result = await tool_calling_agent_flow.execute("Use tools")
            
            assert result == "Error: Tool error"
    
    @pytest.mark.asyncio
    async def test_execute_logs_error(self, tool_calling_agent_flow, caplog):
        """Test that errors are logged"""
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = Exception("Tool error")
            
            await tool_calling_agent_flow.execute("Use tools")
            
            assert "ToolCallingAgent execution failed: Tool error" in caplog.text


class TestFlowIntegration:
    """Integration tests for flows"""
    
    @pytest.mark.asyncio
    async def test_all_flows_implement_base_flow(self):
        """Test that all flow classes properly implement BaseFlow"""
        mock_model = Mock(spec=OpenAIServerModel)
        mock_tools = [Mock(spec=Tool)]
        
        # Mock the agent classes to focus on flow interface testing
        with patch('athos.core.flows.CodeAgent') as mock_code_agent, \
             patch('athos.core.flows.ToolCallingAgent') as mock_tool_agent:
            
            # Test that all flows can be instantiated and have execute method
            flows = [
                ChatbotFlow(model=mock_model),
                CodeAgentFlow(model=mock_model, tools=mock_tools),
                ToolCallingAgentFlow(model=mock_model, tools=mock_tools)
            ]
            
            for flow in flows:
                assert isinstance(flow, BaseFlow)
                assert hasattr(flow, 'execute')
                assert asyncio.iscoroutinefunction(flow.execute)


# Fixtures for pytest configuration
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()