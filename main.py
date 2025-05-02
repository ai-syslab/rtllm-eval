#!/usr/bin/env python3
"""
Main entry point for Verilog generation tools.

This module provides command-line interface to run different Verilog generation methods:
1. Basic generation
2. RAG-enhanced generation
3. Agentic flow with iterative improvement

Usage examples:
    # Basic generation for all categories (default openai)
    python main.py -g
    
    # RAG-enhanced generation for all categories (default openai)
    python main.py -r
    
    # Agentic flow with 5 iterations for all categories (default openai)
    python main.py -a 5
    
    # Basic generation for specific category
    python main.py -g -d Arithmetic

    # Basic generation for specific design 
    python main.py -g -d Arithmetic/Adder/adder_8bit
    
    # RAG-enhanced generation with custom model and temperature
    python main.py -r --model anthropic --temperature 0.5
"""

from pathlib import Path
import argparse
import os
from typing import Optional, List, Any

# Import LLM providers
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.embeddings.openai import OpenAIEmbeddings

# Import our modules
from run_verilog_generation_agent.setup_verilog_generation_agent import (
    setup_agent, ModelConfig, AgentConfig, create_logger
)
from run_verilog_generation_agent.basic_verilog_generation import basic_generation
from run_verilog_generation_agent.rag_verilog_generation import rag_generation
from run_verilog_generation_agent.agentic_verilog_generation import run_agentic_generation

def process_rtllm_directory(
    category_dir: Path,
    logger: Any,
    args: argparse.Namespace,
    model_config: ModelConfig
) -> None:
    """
    Process all test cases in a given RTLLM category directory.
    
    Args:
        category_dir: Directory containing test cases
        logger: Logger instance
        args: Command line arguments
        model_config: Model configuration
    """
    # Check if current directory has design_description.txt
    design_file = category_dir / "design_description.txt"
    if design_file.exists():
        print(f"\nProcessing test case: {category_dir.name}")
        process_test_case(category_dir, design_file, logger, args, model_config)
        return
        
    # Recursively process subdirectories
    for subdir in category_dir.iterdir():
        if subdir.is_dir():
            process_rtllm_directory(subdir, logger, args, model_config)

def process_test_case(
    test_dir: Path,
    design_file: Path,
    logger: Any,
    args: argparse.Namespace,
    model_config: ModelConfig
) -> None:
    """
    Process a single test case directory.
    
    Args:
        test_dir: Directory containing the test case
        design_file: Path to design_description.txt
        logger: Logger instance
        args: Command line arguments
        model_config: Model configuration
    """
    if args.generate:
        basic_generation(logger, model_config, working_dir=test_dir)
        
    elif args.rag:
        rag_generation(logger, model_config, working_dir=test_dir)
        
    elif args.agentic_flow > 0:
        # Setup agent configuration
        agent_config = AgentConfig(
            max_loops=args.agentic_flow,
            design_prompt=design_file.read_text(),
            verilog_reflection_prompt=(
                "The verilog design failed testing. "
                "Please analyze the error and suggest specific fixes."
            ),
            working_dir=test_dir
        )
        run_agentic_generation(logger, model_config, agent_config)

def get_rtllm_categories(rtllm_dir: Path) -> List[Path]:
    """
    Get list of RTLLM category directories.
    
    Args:
        rtllm_dir: Root RTLLM directory
        
    Returns:
        List of category directory paths
    """
    categories = []
    for path in rtllm_dir.iterdir():
        if path.is_dir() and not path.name.startswith('.'):
            categories.append(path)
    return sorted(categories)

def main() -> None:
    """Main entry point for the Verilog generation tools."""
    parser = argparse.ArgumentParser(
        description="Generate and test Verilog designs using various methods"
    )
    
    # Generation method arguments
    method_group = parser.add_mutually_exclusive_group(required=True)
    method_group.add_argument(
        '-g', '--generate',
        action="store_true",
        help="Use basic generation"
    )
    method_group.add_argument(
        '-r', '--rag',
        action="store_true",
        help="Use RAG-enhanced generation"
    )
    method_group.add_argument(
        '-a', '--agentic_flow',
        type=int,
        default=0,
        help="Use agentic flow with specified maximum iterations"
    )
    
    # Directory selection
    parser.add_argument(
        '-d', '--directory',
        type=str,
        help="Specific RTLLM subdirectory to process (e.g., 'Arithmetic', 'Control')"
    )
    
    # Model configuration
    parser.add_argument(
        '--model',
        type=str,
        default='openai',
        choices=['openai', 'anthropic', 'gemini'],
        help="LLM provider to use"
    )
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help="Temperature parameter for the LLM"
    )
    
    args = parser.parse_args()
    print(f"Starting Verilog generation with args: {args}")

    # Create single logger for entire run
    logger = create_logger()
    print("Logger created")
    
    # Test logging
    logger.info("This is a test log message")
    print("Test log message written")
    
    # Setup working directory
    workspace_dir = Path(__file__).parent
    rtllm_dir = workspace_dir / "RTLLM"
    print(f"Looking for RTLLM directory at: {rtllm_dir}")
    
    if not rtllm_dir.exists():
        print(f"Error: RTLLM directory not found at {rtllm_dir}")
        return
        
    # Get categories to process
    if args.directory:
        category_dir = rtllm_dir / args.directory
        print(f"Processing specific category: {category_dir}")
        if not category_dir.exists():
            print(f"Error: Category directory {args.directory} not found")
            return
        categories = [category_dir]
    else:
        categories = get_rtllm_categories(rtllm_dir)
        print(f"Found categories: {[c.name for c in categories]}")
        
    # Process each category
    for category_dir in categories:
        print(f"\nProcessing category: {category_dir.name}")
        
        # Setup for this category
        model_config, agent_config = setup_agent(
            working_dir=category_dir,
            model_provider=args.model,
            temperature=args.temperature,
            max_loops=args.agentic_flow if args.agentic_flow > 0 else 3,
            logger=logger
        )
        print(f"Setup complete for {category_dir.name}")
        
        # Process all test cases in this category
        process_rtllm_directory(category_dir, logger, args, model_config)
        print(f"Finished processing {category_dir.name}")

if __name__ == "__main__":
    main()