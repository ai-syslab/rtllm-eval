#!/usr/bin/env python3
"""
Agentic Verilog design generator

This module implements an agentic flow that:
1. Generates initial Verilog design
2. Tests the design using Icarus
3. If tests fail, reflects on errors and iteratively improves the design
"""

from pathlib import Path
from typing import TypedDict, Annotated, Optional, List, Tuple, Any
import operator
import asyncio
from fastmcp import Client
from mcp import types

from langchain_core.messages import (
    AnyMessage, SystemMessage, HumanMessage, ChatMessage
)
from langgraph.graph import StateGraph, START, END
import subprocess

from .setup_verilog_generation_agent import ModelConfig, AgentConfig

class AgentState(TypedDict):
    """State maintained throughout the agent's execution."""
    messages: Annotated[list[AnyMessage], operator.add]

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

class VerilogGenerationAgent:
    """Agent that manages the iterative Verilog design generation process."""
    
    def __init__(
        self, 
        logger: Any,
        model_config: ModelConfig,
        agent_config: AgentConfig
    ):
        self.logger = logger
        self.model_config = model_config
        self.config = agent_config
        self.curr_loop = 1
        self.conversation: List[AnyMessage] = []
        
        # Initialize conversation
        self.conversation = [
            SystemMessage(content=self.model_config.system_prompt),
            HumanMessage(content=self.config.design_prompt)
        ]
        
        # Log start
        self.logger.warning("Verilog Generation Begin")
        self.logger.info(f"Starting Prompt:\n{self.config.design_prompt}\n")
        
        # Setup graph
        self.graph = self._setup_graph()

    def _setup_graph(self) -> Any:
        """Set up the LangGraph execution graph."""
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("design_generation", self.design_generation)
        graph.add_node("end_graph", self.end_graph)
        
        # Add edges
        graph.add_conditional_edges(
            "design_generation",
            self.verilog_test,
            {1: "design_generation", 2: "end_graph"}
        )
        graph.add_edge(START, "design_generation")
        graph.add_edge("end_graph", END)
        
        # Set entry point
        graph.set_entry_point("design_generation")
        
        return graph.compile()


    def design_generation(self, state: AgentState) -> dict:
        """Generate Verilog design based on prompt and context."""
        print("\nSending prompt to LLM...")
        self.logger.info(f"Generation Prompt:\n{self.config.design_prompt}\n")
        
        message = self.model_config.generation_client.invoke(self.conversation).content
        print("Received response from LLM")
        module = extract_module_content(message)
        
        self.logger.info(f"Generated Design:\n{module}\n")
        
        # Update conversation history
        if len(self.conversation) >= 4:
            self.conversation[2] = ChatMessage(role='assistant', content=message)
            self.conversation = self.conversation[0:2]
        else:
            self.conversation.append(ChatMessage(role='assistant', content=message))
            
        # Save design
        print("Writing generated Verilog to file...")
        design_file = self.config.working_dir / "design.v"
        design_file.write_text(module)
        print(f"Wrote Verilog to {design_file}")
        
        return {'messages': [message]}

    async def _verilog_test_mcp(self) -> tuple[str, bool]:
        """Test the generated Verilog design using MCP client."""
        try:
            async with Client("http://localhost:8000/sse") as client:
                result = await client.call_tool(
                    "run_verilog_tests",
                    {"working_dir": str(self.config.working_dir)}
                )
                
                # Convert TextContent to string for output
                if isinstance(result[0], types.TextContent):
                    output = str(result[0])
                else:
                    output = str(result[0])
                    
                return output, True
                
        except Exception as e:
            error_msg = f"Error running tests: {str(e)}"
            self.logger.error(error_msg)
            return error_msg, False

    def verilog_test(self, state: AgentState) -> int:
        """Test the generated Verilog design and handle failures."""
        self.logger.info("Testing Verilog Design")
        print("\nVerilog Test:")
        
        # Run tests using MCP client
        msg, success = asyncio.run(self._verilog_test_mcp())
        print(f"Test Output:\n{msg}\n")
        
        # Write results
        self._write_results(msg)
        
        # Check if tests passed
        if "passed" in msg.lower():
            return 2
            
        # Check if we've exceeded max loops
        if self.curr_loop >= self.config.max_loops:
            return 2
            
        # Increment loop counter
        self.curr_loop += 1
            
        # Handle test failure with reflection
        return self._handle_test_failure(msg)

    def _handle_test_failure(self, error_msg: str) -> int:
        """Handle test failure by getting LLM reflection and updating prompt."""
        reflection_prompt = f"{self.config.verilog_reflection_prompt}\nError: {error_msg}"
        print(f"\nReflection Prompt:\n{reflection_prompt}\n")
        
        user_input = input("\nContinue with reflection? (Y/N): ").upper()
        if user_input != 'Y':
            return 2
            
        self.conversation.append(HumanMessage(content=reflection_prompt))
        reflection = self.model_config.reflection_client.invoke(self.conversation).content
        
        print(f"\nLLM Reflection:\n{reflection}\n")
        
        user_input = input("\nContinue with design modification? (Y/N): ").upper()
        if user_input != 'Y':
            return 2
            
        new_prompt = (
            f'Modify the verilog design using these suggestions: """{reflection}"""\n'
            f'Generate verilog code only. Do not explain changes.'
        )
        
        self.conversation.append(HumanMessage(content=new_prompt))
        self.config.design_prompt = new_prompt
        
        return 1  # Return 1 to continue the loop

    def _write_results(self, test_output: str) -> None:
        """Write test results and current state to output file."""
        passed = "passed" in test_output.lower()
        status = "Passed" if passed else "Failed"
        
        output_content = f"""Test Results:
Status: Design {status}

Current Iteration: {self.curr_loop} of {self.config.max_loops}

Test Output:
{test_output}

Current Conversation History:
{self._format_conversation()}
"""
        
        output_file = self.config.working_dir / "output.txt"
        if self.curr_loop == 1:
            # First iteration - create new file
            output_file.write_text(output_content)
        else:
            # Subsequent iterations - append to file
            with output_file.open('a') as f:
                f.write("\n" + "="*80 + "\n")  # Add separator between iterations
                f.write(output_content)

    def _format_conversation(self) -> str:
        """Format conversation history for output file."""
        return "\n\n".join(
            f"{msg.__class__.__name__}:\n{msg.content}"
            for msg in self.conversation
        )

    def end_graph(self, state: AgentState) -> dict:
        """Handle end of execution."""
        # Run final test to show results
        self.logger.info("Running final test")
        
        # Run tests
        compile_cmd = ["iverilog", "-o", "netlist.vvp", "design.v", "testbench.v"]
        run_cmd = ["vvp", "netlist.vvp"]
        
        # Compile design
        result = subprocess.run(
            compile_cmd, 
            capture_output=True, 
            text=True,
            cwd=self.config.working_dir
        )
        
        if result.returncode != 0:
            self.logger.error(f"Final Compilation Error:\n{result.stderr}\n")
            msg = result.stderr
        else:
            # Run tests
            result = subprocess.run(
                run_cmd, 
                capture_output=True, 
                text=True,
                cwd=self.config.working_dir
            )
            
            if result.returncode != 0:
                self.logger.error(f"Final Runtime Error:\n{result.stderr}\n")
                msg = result.stderr
            else:
                msg = result.stdout
        
        # Write final results
        self._write_results(msg)
        print(f"\nFinal Test Results:\n{msg}\n")
        
        self.logger.info("Verilog Generation Complete")
        return {"messages": [SystemMessage(content="End graph")]}

def run_agentic_generation(
    logger: Any,
    model_config: ModelConfig,
    agent_config: AgentConfig
) -> None:
    """
    Run the agentic Verilog generation process.
    
    Args:
        logger: Logger instance for recording the process
        model_config: Configuration for the LLM models
        agent_config: Configuration for the agent's behavior
    """
    agent = VerilogGenerationAgent(logger, model_config, agent_config)
    agent.graph.invoke({"messages": []})