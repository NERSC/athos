#!/usr/bin/env python3

import sys
import os

from athos.agents.smolagent_hpc import HPCSmolAgent

def main():
    print("Testing HPC SmolAgent...")
    print("-" * 40)
    
    try:
        # Create and run the agent
        agent = HPCSmolAgent()
        agent.run()
        print("-" * 40)
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"Error running HPC agent: {e}")
        print(f"Error type: {type(e).__name__}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())