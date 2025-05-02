#!/usr/bin/env python3
"""
RAG-enhanced Verilog design generator based on prompts from RTLLM dataset.

This module uses RAG (Retrieval Augmented Generation) methods to find similar existing
designs and uses them to improve the generation of new Verilog designs.
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.vectorstores import Chroma
import os
import subprocess

from .setup_verilog_generation_agent import ModelConfig

SYSTEM_PROMPT = """You are an assistant that can generate code based on prompts. 
Your responses should only consist of verilog code when asked to generate a verilog module. 
When generating verilog, use the Verilog-1995 standard."""

def extract_module_content(message: str) -> str:
    """Extract the Verilog module content from the LLM response."""
    if 'module' not in message:
        return ""
        
    lines = message.splitlines()
    
    # Find start of module
    start_idx = next(
        (i for i, line in enumerate(lines) 
         if 'module' in line.split()), 0
    )
    
    # Find end of module
    end_idx = next(
        (i for i, line in enumerate(reversed(lines))
         if 'endmodule' in line.split()), 
        len(lines)-1
    )
    end_idx = len(lines) - end_idx - 1
    
    return "\n".join(lines[start_idx:end_idx+1])

def run_verilog_tests(working_dir: Path, logger) -> tuple[bool, str]:
    """Compile and run Verilog tests using Icarus in the specified directory."""
    compile_cmd = ["iverilog", "-o", "netlist.vvp", "design.v", "testbench.v"]
    run_cmd = ["vvp", "netlist.vvp"]
    
    logger.info("Testing Verilog Design")
    print("\n\nVerilog Test:")
    
    # Compile design
    result = subprocess.run(
        compile_cmd, 
        capture_output=True, 
        text=True,
        cwd=working_dir
    )
    if result.returncode != 0:
        error_msg = f"Compilation Error:\n{result.stderr}"
        print(f"{error_msg}\n\n")
        logger.error(error_msg)
        return False, result.stderr
        
    # Run tests
    result = subprocess.run(
        run_cmd, 
        capture_output=True, 
        text=True,
        cwd=working_dir
    )
    if result.returncode != 0:
        error_msg = f"Runtime Error:\n{result.stderr}"
        print(f"{error_msg}\n\n")
        logger.error(error_msg)
        return False, result.stderr
    
    print(f"Test Output:\n{result.stdout}\n\n")
    return True, result.stdout

def get_similar_design(prompt: str, model_config: ModelConfig, logger) -> Tuple[str, str]:
    """
    Find similar designs using RAG and return the most relevant one.
    
    Args:
        prompt: Design prompt to find similar designs for
        model_config: Model configuration with embeddings and RAG settings
        logger: Logger instance
        
    Returns:
        Tuple of (similar design content, similarity score)
    """
    try:
        # Create vector store
        vectorstore = Chroma(
            persist_directory=model_config.rag_persist_directory,
            embedding_function=model_config.embeddings
        )
        
        # Find similar designs
        docs = vectorstore.similarity_search_with_score(prompt, k=1)
        if not docs:
            print("\nNo similar designs found in RAG dataset")
            logger.warning("No similar designs found in RAG dataset")
            return "", "0.0"
            
        similar_design, score = docs[0]
        print(f"\nFound similar design with score: {score}")
        logger.info(f"Found similar design with score: {score}")
        
        return similar_design.page_content, str(score)
        
    except Exception as e:
        print(f"\nError in RAG search: {str(e)}")
        logger.error(f"Error in RAG search: {str(e)}")
        return "", "0.0"

def rag_generation(logger, model_config: ModelConfig, working_dir: Path = None) -> None:
    """
    Generate Verilog design using RAG-enhanced generation.
    
    Args:
        logger: Logger instance
        model_config: Model configuration
        working_dir: Directory containing design files
    """
    if working_dir is None:
        working_dir = Path.cwd()
        
    design_file = working_dir / "design_description.txt"
    if not design_file.exists():
        logger.error(f"design_description.txt not found in {working_dir}")
        return
        
    design_prompt = design_file.read_text()
    
    # Get similar design using RAG
    similar_design, similarity_score = get_similar_design(
        design_prompt, model_config, logger
    )
    
    # Prepare enhanced prompt
    enhanced_prompt = f"""Design Prompt:
{design_prompt}

Similar Existing Design (similarity score: {similarity_score}):
{similar_design}

Please generate a new Verilog design based on the design prompt above.
Use the similar design as a reference but ensure your design meets the requirements
specified in the prompt."""
    
    # Generate Verilog using LLM
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=enhanced_prompt)
    ]
    
    try:
        response = model_config.generation_client.invoke(messages)
        verilog_code = extract_module_content(response.content)
        
        if not verilog_code:
            logger.error("No Verilog module found in LLM response")
            return
            
        # Write generated Verilog to file
        output_file = working_dir / "design.v"
        output_file.write_text(verilog_code)
        logger.info(f"Generated Verilog written to {output_file}")
        
        # Run tests
        success, error_msg = run_verilog_tests(working_dir, logger)
        if success:
            logger.info("Verilog design passed all tests")
        else:
            logger.error(f"Verilog design failed tests: {error_msg}")
            
    except Exception as e:
        logger.error(f"Error during generation: {str(e)}")