#!/usr/bin/env python3
"""
Setup utilities for Verilog generation tools.

This module provides configuration and setup functionality for:
1. Logging setup
2. Model configuration
3. Loading design and reflection prompts
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Tuple, Optional
import logging
import yaml
import os

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI # poetry add langchain-openai
from langchain_anthropic import ChatAnthropic # poetry add langchain-anthropic
from langchain_google_genai import ChatGoogleGenerativeAI # poetry add langchain-google-genai 
from langchain.embeddings.openai import OpenAIEmbeddings

# Get the directory of this file
CURRENT_DIR = Path(__file__).parent

@dataclass
class ModelConfig:
    """Configuration for the LLM models."""
    generation_client: BaseChatModel
    reflection_client: BaseChatModel
    embeddings: OpenAIEmbeddings
    rag_persist_directory: str

@dataclass
class AgentConfig:
    """Configuration for the agent's behavior."""
    max_loops: int
    design_prompt: str
    verilog_reflection_prompt: str
    working_dir: Path

def create_logger(name: str = 'Verilog Generation Tool') -> logging.Logger:
    """
    Create and configure a logger for the Verilog generation process.
    
    Args:
        name: Name for the logger instance
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = CURRENT_DIR.parent / "logging"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"{timestamp}.log"
    log_file.touch()
    
    # Configure handler
    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8"
    )
    
    # Set formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger

def load_reflection_prompt(config_dir: Path = CURRENT_DIR.parent.parent / "config") -> str:
    """
    Load reflection prompt from YAML configuration.
    
    Args:
        config_dir: Path to the config directory
        
    Returns:
        Reflection prompt string
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        KeyError: If required key is missing from config
    """
    prompt_file = config_dir / "reflection_prompt.yml"
    
    if not prompt_file.exists():
        raise FileNotFoundError(
            f"Reflection prompt config not found at {prompt_file}"
        )
        
    with prompt_file.open('r') as f:
        config = yaml.safe_load(f)
        
    if 'verilog_reflection_prompt' not in config:
        raise KeyError(
            "verilog_reflection_prompt not found in config file"
        )
        
    return config['verilog_reflection_prompt']

def create_model_config(
    provider: str = "openai",
    temperature: float = 0.7,
    rag_dir: str = str(CURRENT_DIR.parent.parent / "rag_dataset" / "chroma")
) -> ModelConfig:
    """
    Create model configuration for specified provider.
    
    Args:
        provider: Model provider ('openai', 'anthropic', or 'gemini')
        temperature: Temperature parameter for generation
        rag_dir: Directory for RAG dataset
        
    Returns:
        ModelConfig instance
        
    Raises:
        ValueError: If provider is invalid
    """
    # Create embeddings for RAG
    embeddings = OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Setup provider-specific clients
    if provider == "openai":
        generation_client = ChatOpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            model="gpt-4o",
            temperature=temperature
        )
        reflection_client = ChatOpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            model="gpt-4o",
            temperature=temperature
        )
    elif provider == "anthropic":
        generation_client = ChatAnthropic(
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            model="claude-3-sonnet-20240229",
            temperature=temperature
        )
        reflection_client = ChatAnthropic(
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            model="claude-3-sonnet-20240229",
            temperature=temperature
        )
    elif provider == "gemini":
        generation_client = ChatGoogleGenerativeAI(
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            model="gemini-pro",
            temperature=temperature
        )
        reflection_client = ChatGoogleGenerativeAI(
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            model="gemini-pro",
            temperature=temperature
        )
    else:
        raise ValueError(f"Invalid model provider: {provider}")
            
    return ModelConfig(
        generation_client=generation_client,
        reflection_client=reflection_client,
        embeddings=embeddings,
        rag_persist_directory=rag_dir
    )

def setup_agent(
    working_dir: Path,
    model_provider: str = "openai",
    temperature: float = 0.7,
    max_loops: int = 3,
    logger: Optional[logging.Logger] = None
) -> Tuple[ModelConfig, AgentConfig]:
    """
    Set up all components needed for Verilog generation.
    
    Args:
        working_dir: Directory containing design files
        model_provider: LLM provider to use
        temperature: Temperature for generation
        max_loops: Maximum iterations for agentic flow
        logger: Existing logger to use (optional)
        
    Returns:
        Tuple of (model config, agent config)
    """
    # Load configurations
    config_dir = CURRENT_DIR.parent / "config"
    reflection_prompt = load_reflection_prompt(config_dir)
    
    # Setup model
    model_config = create_model_config(
        model_provider,
        temperature
    )
    
    # Create agent config with empty design prompt - it will be set in process_rtllm_directory
    agent_config = AgentConfig(
        design_prompt="",  # Will be set when processing individual test cases
        verilog_reflection_prompt=reflection_prompt,
        max_loops=max_loops,
        working_dir=working_dir
    )
    
    return model_config, agent_config