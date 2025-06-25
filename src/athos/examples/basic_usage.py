"""
NONWORKING DEPRECATED EXAMPLE.
Demonstrates some possible use-cases with athos, but these are not fully implemented.
"""
import asyncio
import sys
import os

from athos.core.manager import create_athos_manager

async def basic_chatbot_example():
    """Example of using the HPC chatbot flow"""
    print("=== Basic Chatbot Example ===")
    
    # Create ATHOS agent from configuration
    agent = create_athos_manager("config.yaml")
    
    # List available flows
    print("Available flows:", agent.list_flows())
    
    # Use the chatbot flow
    questions = [
        "What is SLURM and how do I submit a job?",
        "How can I check my disk quota?",
        "What are the best practices for parallel computing?",
        "How do I optimize memory usage in my HPC application?"
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        response = await agent.execute_flow("hpc_chatbot", question)
        print(f"Answer: {response}")

async def code_agent_example():
    """Example of using the code agent flow"""
    print("\n=== Code Agent Example ===")
    
    agent = create_athos_manager("config.yaml")
    
    # Example tasks for the code agent
    tasks = [
        "Check the current system load and memory usage",
        "List all running SLURM jobs for user 'john'",
        "Show me the available modules on the system",
        "Check disk usage for the /scratch directory"
    ]
    
    for task in tasks:
        print(f"\nTask: {task}")
        result = await agent.execute_flow("hpc_automation", task)
        print(f"Result: {result}")

async def problem_solving_example():
    """Example of using the problem-solving prompt chain"""
    print("\n=== Problem Solving Example ===")
    
    agent = create_athos_manager("config.yaml")
    
    # Example problem scenarios
    problems = [
        "My MPI job is running much slower than expected on 32 cores",
        "Users are complaining about slow I/O performance when accessing shared storage",
        "A compute node keeps going offline with memory errors"
    ]
    
    for problem in problems:
        print(f"\nProblem: {problem}")
        result = await agent.execute_flow("problem_solver", problem)
        
        print("=== Diagnosis ===")
        print(result.get("diagnose", "No diagnosis available"))
        
        print("\n=== Proposed Solution ===")
        print(result.get("propose_solution", "No solution available"))
        
        print("\n=== Reflection ===")
        print(result.get("reflection", "No reflection available"))
        print("-" * 80)

async def performance_optimization_example():
    """Example of using the performance optimization flow"""
    print("\n=== Performance Optimization Example ===")
    
    agent = create_athos_manager("config.yaml")
    
    # Example performance issues
    scenarios = [
        "My molecular dynamics simulation is not scaling well beyond 16 cores",
        "CFD application shows poor memory bandwidth utilization",
        "Machine learning training job has inconsistent GPU utilization"
    ]
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario}")
        result = await agent.execute_flow("performance_optimizer", scenario)
        
        print("=== Performance Analysis ===")
        print(result.get("analyze_performance", "No analysis available"))
        
        print("\n=== Optimization Strategy ===")
        print(result.get("optimization_strategy", "No strategy available"))
        print("-" * 80)

async def main():
    """Run all examples"""
    try:
        await basic_chatbot_example()
        await code_agent_example()
        await problem_solving_example()
        await performance_optimization_example()
    except Exception as e:
        print(f"Error running examples: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

