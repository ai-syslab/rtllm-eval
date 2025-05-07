#!/usr/bin/env python3
"""
RAG-enhanced Verilog design generator based on prompts from RTLLM dataset.

This module uses RAG (Retrieval Augmented Generation) methods to find similar existing
designs and uses them to improve the generation of new Verilog designs.
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.vectorstores import Chroma
import os
import asyncio
from fastmcp import Client
from mcp import types

from .setup_verilog_generation_agent import ModelConfig
from .setup_rag import setup_rag_database

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

async def run_verilog_tests_mcp(working_dir: Path, logger) -> tuple[bool, str]:
    """Test the generated Verilog design using MCP client."""
    try:
        async with Client("http://localhost:8000/sse") as client:
            result = await client.call_tool(
                "run_verilog_tests",
                {"working_dir": str(working_dir)}
            )
            
            # Convert TextContent to string for output
            if isinstance(result[0], types.TextContent):
                output = str(result[0])
            else:
                output = str(result[0])
                
            return True, output
            
    except Exception as e:
        error_msg = f"Error running tests: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def run_verilog_tests(working_dir: Path, logger) -> tuple[bool, str]:
    """Compile and run Verilog tests using MCP client."""
    return asyncio.run(run_verilog_tests_mcp(working_dir, logger))

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
        # Check if database exists
        persist_dir = Path(model_config.rag_persist_directory)
        print(f"\nChecking RAG database at: {persist_dir}")
        logger.info(f"Checking RAG database at: {persist_dir}")
        
        # Check if directory exists and has content
        if not persist_dir.exists():
            print(f"RAG database directory does not exist at {persist_dir}")
            logger.info(f"RAG database directory does not exist at {persist_dir}")
            needs_setup = True
        elif not any(persist_dir.iterdir()):
            print(f"RAG database directory is empty at {persist_dir}")
            logger.info(f"RAG database directory is empty at {persist_dir}")
            needs_setup = True
        else:
            print(f"Found existing RAG database at {persist_dir}")
            logger.info(f"Found existing RAG database at {persist_dir}")
            needs_setup = False
            
        if needs_setup:
            print("\nRAG database not found. Setting up database...")
            logger.info("RAG database not found. Setting up database...")
            try:
                setup_rag_database(str(persist_dir))
                print("RAG database setup complete.")
                logger.info("RAG database setup complete.")
            except Exception as e:
                error_msg = f"Failed to set up RAG database: {str(e)}"
                print(f"\n{error_msg}")
                logger.error(error_msg)
                return "", "0.0"
        
        # Create vector store
        print("\nConnecting to RAG database...")
        vectorstore = Chroma(
            persist_directory=model_config.rag_persist_directory,
            embedding_function=model_config.embeddings
        )
        
        # Find similar designs
        print("Searching for similar designs...")
        docs = vectorstore.similarity_search_with_score(prompt, k=1)
        if not docs:
            print("\nNo similar designs found in RAG dataset")
            logger.warning("No similar designs found in RAG dataset")
            return "", "0.0"
            
        similar_design, score = docs[0]
        print(f"\nFound similar design with score: {score}")
        logger.info(f"Found similar design with score: {score}")
        
        # Extract summary and code from the content
        content = similar_design.page_content
        if "Summary:" in content and "Verilog Implementation:" in content:
            summary, code = content.split("Verilog Implementation:")
            summary = summary.replace("Summary:", "").strip()
            code = code.strip()
        else:
            # Fallback for old format
            summary = content
            code = similar_design.metadata.get("code", "")
        
        return f"Summary: {summary}\n\nCode:\n{code}", str(score)
        
    except Exception as e:
        error_msg = f"Error in RAG search: {str(e)}"
        print(f"\n{error_msg}")
        logger.error(error_msg)
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
    print("\nSearching for similar designs...")
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
        SystemMessage(content=model_config.system_prompt),
        HumanMessage(content=enhanced_prompt)
    ]
    
    try:
        print("\nSending prompt to LLM...")
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
        print("\n\nVerilog Test:")
        success, error_msg = run_verilog_tests(working_dir, logger)
        if success:
            print(f"Test Output:\n{error_msg}\n\n")
            logger.info("Verilog design passed all tests")
        else:
            print(f"Test Output:\n{error_msg}\n\n")
            logger.error(f"Verilog design failed tests: {error_msg}")
            
    except Exception as e:
        logger.error(f"Error during generation: {str(e)}")