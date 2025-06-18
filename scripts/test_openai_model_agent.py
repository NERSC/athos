#!/usr/bin/env python3
"""
Test script demonstrating usage of OpenAIModelAgent.

This script shows various ways to use the OpenAIModelAgent for text generation
and conversation tasks without tool calling capabilities.
"""

import os
from athos.agents.openai_agent import OpenAIModelAgent


def test_basic_usage():
    """Test basic prompt-response functionality."""
    print("=== Basic Usage Test ===")
    
    # Initialize the agent
    agent = OpenAIModelAgent(model="gpt-3.5-turbo")
    
    # Simple prompt
    prompt = "What is the capital of France?"
    response = agent.run(prompt)
    print(f"Prompt: {prompt}")
    print(f"Response: {response}")
    print()


def test_generate_response():
    """Test the generate_response method directly."""
    print("=== Generate Response Test ===")
    
    agent = OpenAIModelAgent(model="gpt-3.5-turbo")
    
    prompt = "Explain quantum computing in simple terms."
    response = agent.generate_response(prompt, max_tokens=100)
    print(f"Prompt: {prompt}")
    print(f"Response: {response}")
    print()


def test_chat_completion():
    """Test the chat_completion method with conversation history."""
    print("=== Chat Completion Test ===")
    
    agent = OpenAIModelAgent(model="gpt-3.5-turbo")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant that speaks like a pirate."},
        {"role": "user", "content": "Tell me about the weather."},
        {"role": "assistant", "content": "Ahoy! I be needin' to know yer location to tell ye about the weather, matey!"},
        {"role": "user", "content": "I'm in San Francisco."}
    ]
    
    response = agent.chat_completion(messages, max_tokens=150)
    print("Conversation:")
    for msg in messages:
        print(f"{msg['role'].title()}: {msg['content']}")
    print(f"Assistant: {response.choices[0].message.content}")
    print()


def test_with_parameters():
    """Test with various OpenAI API parameters."""
    print("=== Parameters Test ===")
    
    agent = OpenAIModelAgent(model="gpt-3.5-turbo")
    
    prompt = "Write a haiku about programming."
    response = agent.run(
        prompt,
        temperature=0.8,
        max_tokens=50,
        top_p=0.9
    )
    print(f"Prompt: {prompt}")
    print(f"Response: {response}")
    print()


def test_different_models():
    """Test with different OpenAI models."""
    print("=== Different Models Test ===")
    
    models = ["gpt-3.5-turbo", "gpt-4"]
    prompt = "What is artificial intelligence?"
    
    for model in models:
        try:
            agent = OpenAIModelAgent(model=model)
            response = agent.run(prompt, max_tokens=80)
            print(f"Model: {model}")
            print(f"Response: {response}")
            print()
        except Exception as e:
            print(f"Error with model {model}: {e}")
            print()


def test_conversation_flow():
    """Test a multi-turn conversation simulation."""
    print("=== Conversation Flow Test ===")
    
    agent = OpenAIModelAgent(model="gpt-3.5-turbo")
    
    # Simulate a conversation by building message history
    conversation = [
        {"role": "system", "content": "You are a knowledgeable tutor helping with math problems."}
    ]
    
    user_inputs = [
        "I need help with algebra.",
        "How do I solve 2x + 5 = 15?",
        "Can you explain the steps?"
    ]
    
    for user_input in user_inputs:
        # Add user message
        conversation.append({"role": "user", "content": user_input})
        
        # Get response
        response = agent.chat_completion(conversation, max_tokens=150)
        assistant_response = response.choices[0].message.content
        
        # Add assistant response to conversation
        conversation.append({"role": "assistant", "content": assistant_response})
        
        print(f"User: {user_input}")
        print(f"Assistant: {assistant_response}")
        print()


def main():
    """Run all test functions."""
    print("OpenAIModelAgent Test Script")
    print("=" * 40)
    
    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("Make sure to set your OpenAI API key before running this script.")
        print()
    
    try:
        test_basic_usage()
        test_generate_response()
        test_chat_completion()
        test_with_parameters()
        test_different_models()
        test_conversation_flow()
        
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        print("Make sure you have a valid OpenAI API key and internet connection.")


if __name__ == "__main__":
    # print('main')
    main()