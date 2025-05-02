# Agentic AI RTL Design
Project Overview:
 - This project is meant to test different methods of improve LLM verilog generation
 - The RTLLM benchmark is used to test generation methods - https://github.com/hkust-zhiyao/RTLLM
 - All verilog code is generated in Verilog-1995 so Icarus Verilog compiler can be used to verify the code's functionality
 - There are 3 methods of generation tested:
   - basic generation: the LLM is given a prompt from the RTLLM dataset and told to generate a Verilog script
   - RAG generation: the project uses Retrieval Augmented Generation to imporove code generation. The following repo is used to augment the LLM - https://github.com/GATECH-EIC/mg-verilog
   - Agentic flow generation: the project uses RAG generation during the first iteration of the agentic flow. If generation fails, the LLM is asked to reflect on why it failed and what could be fixed. This reflection is used to generate a new verilog script


Design tools:

Icarus:
 - Install setup file from https://bleyer.org/icarus/
 - During setup, install iverilog and gtkwave


Setup instructions:
 - add openai api key to environment variables as 'OPENAI_API_KEY'
 - clone repository
 - poetry is used for dependeny management
 - poetry intall to install dependencies listed in pyproject.toml
 - In config directory, change reflection prompt for agentic flow in the reflection_prompt.yml file if necessary

Usage Instructions (Refer to the example at the bottom of the README if you are stuck):
 - Within the terminal, navigate to desired RTLLM prompt in RTLLM_Agentic/RTLLM
 - run main.py from RTLLM folder containing desired design: python ../../../../main.py
   - To use basic generation: add "-g" flag in command
   - To use RAG generation, add "-r" flag in command
   - To use agentic flow generation, add "-a 1" flag with the number denoting how many times the agentic flow should regenerate and retest the verilog module if the test fails
 - Generated verilog design is stored within current folder
 - Each run of the project creates a new log file in the logging folder in the root directory labeled by the date and time it was run
   - the log file details each stage of generation(RAG script used, prompt used, reflection)

Example Run(generate RTLLM design, accu, with basic generation):
 - navigate to RTLLM_Agentic/RTLLM/Arithmetic/Accumulator/accu
 - run command: python ../../../../main.py -g
 - check generation output either in terminal or in RTLLM_Agentic/logging/latest_log.txt (replace "latest_log" with date and time that the project was run
 - find generated verilog script in the "design.v" file in RTLLM_Agentic/RTLLM/Arithmetic/Accumulator/accu

