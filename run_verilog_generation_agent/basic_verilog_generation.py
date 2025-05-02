#!/usr/bin/env python3
"""
Verilog design generator based on prompts from RTLLM dataset.

This module obtains prompts from the RTLLM problem set and uses an LLM
to generate Verilog scripts based on the given prompts.
"""

from pathlib import Path
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
import os
import subprocess

from .setup_verilog_generation_agent import ModelConfig

SYSTEM_PROMPT = """You are an assistant that can generate code based on prompts. 
Your responses should only consist of verilog code when asked to generate a verilog module. 
When generating verilog, use the Verilog-1995 standard."""

def extract_module_content(message: str) -> str:
    """Extract the Verilog module content from the LLM response.
    
    Args:
        message: Raw response from the LLM
        
    Returns:
        str: Extracted module content or empty string if no module found
    """
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
    
    return '\n'.join(lines[start_idx:len(lines)-end_idx])

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

def basic_generation(logger, model_config: ModelConfig, working_dir: Path = None) -> None:
    """
    Generate Verilog design using basic LLM generation.
    
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
    
    # Generate Verilog using LLM
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=design_prompt)
    ]
    
    try:
        print("Sending prompt to LLM...")
        response = model_config.generation_client.invoke(messages)
        print("Received response from LLM")
        verilog_code = extract_module_content(response.content)
        
        if not verilog_code:
            logger.error("No Verilog module found in LLM response")
            print("No Verilog module found in response")
            return
            
        print("Writing generated Verilog to file...")
        # Write generated Verilog to file
        output_file = working_dir / "design.v"
        output_file.write_text(verilog_code)
        logger.info(f"Generated Verilog written to {output_file}")
        print(f"Wrote Verilog to {output_file}")
        
        # Run tests
        success, error_msg = run_verilog_tests(working_dir, logger)
        if success:
            logger.info("Verilog design passed all tests")
        else:
            logger.error(f"Verilog design failed tests: {error_msg}")
            
    except Exception as e:
        logger.error(f"Error during generation: {str(e)}")