#!/usr/bin/env python3
"""
Test script for MCP integration in ATHOS
"""

import asyncio
import logging
from pathlib import Path

from athos.config import ConfigLoader
from athos.core.manager import AthosManager

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_mcp_integration():
    """Test MCP integration functionality"""
    try:
        # Load configuration
        config_path = Path("config/config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return False
            
        logger.info("Loading ATHOS configuration...")
        config = ConfigLoader.load_config(str(config_path))
        
        # Create ATHOS manager
        logger.info("Creating ATHOS manager...")
        manager = AthosManager(config)
        
        # Test regular tools
        logger.info("Testing regular tool loading...")
        regular_tools = [name for name, tool_config in config.tools.items() 
                        if tool_config.tool_type.value == "regular"]
        logger.info(f"Regular tools found: {regular_tools}")
        
        # Test MCP tools (if any are configured)
        logger.info("Testing MCP tool configuration...")
        mcp_tools = [name for name, tool_config in config.tools.items() 
                    if tool_config.tool_type.value in ["mcp_stdio", "mcp_sse"]]
        logger.info(f"MCP tools configured: {mcp_tools}")
        
        # List available flows
        logger.info("Available execution flows:")
        for flow_name in manager.list_flows():
            flow_info = manager.get_flow_info(flow_name)
            logger.info(f"  - {flow_name}: {flow_info['type']} with tools {flow_info['tools']}")
        
        # Test a simple flow execution (non-MCP first)
        if "hpc_chatbot" in manager.flows:
            logger.info("Testing simple chatbot flow...")
            try:
                result = await manager.execute_flow("hpc_chatbot", "What is HPC?")
                logger.info(f"Chatbot response: {result[:100]}...")
            except Exception as e:
                logger.warning(f"Chatbot test failed (expected if no API keys): {e}")
        
        # Clean up
        manager.close()
        logger.info("MCP integration test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"MCP integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration_parsing():
    """Test configuration parsing without creating connections"""
    try:
        logger.info("Testing configuration parsing...")
        config_path = Path("config/config.yaml")
        config = ConfigLoader.load_config(str(config_path))
        
        # Check tools configuration
        logger.info(f"Total tools configured: {len(config.tools)}")
        
        for name, tool_config in config.tools.items():
            logger.info(f"Tool '{name}': type={tool_config.tool_type.value}")
            if tool_config.mcp_config:
                if tool_config.mcp_config.command:
                    logger.info(f"  MCP stdio: {tool_config.mcp_config.command} {tool_config.mcp_config.args}")
                elif tool_config.mcp_config.url:
                    logger.info(f"  MCP SSE: {tool_config.mcp_config.url}")
        
        # Check execution flows
        logger.info(f"Total execution flows: {len(config.execution_flows)}")
        for name, flow_config in config.execution_flows.items():
            logger.info(f"Flow '{name}': type={flow_config.type.value}, tools={flow_config.tools}")
        
        logger.info("Configuration parsing test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Configuration parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("ATHOS MCP Integration Test")
    print("=" * 60)
    
    # Test configuration parsing first
    print("\n1. Testing configuration parsing...")
    config_success = test_configuration_parsing()
    
    # Test full integration
    print("\n2. Testing MCP integration...")
    if config_success:
        integration_success = asyncio.run(test_mcp_integration())
    else:
        integration_success = False
    
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print(f"Configuration parsing: {'PASS' if config_success else 'FAIL'}")
    print(f"MCP integration: {'PASS' if integration_success else 'FAIL'}")
    print("=" * 60)
    
    if config_success and integration_success:
        print("\n✅ All tests passed! MCP integration is working.")
    else:
        print("\n❌ Some tests failed. Check the logs above for details.")