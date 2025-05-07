#!/usr/bin/env python3
"""
Setup script for RAG (Retrieval Augmented Generation) functionality.

This module handles the setup of the ChromaDB vector store with Verilog designs
from the MG-Verilog dataset.
"""

from datasets import load_dataset
from langchain.text_splitter import RecursiveCharacterTextSplitter
#from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
#from langchain.vectorstores import Chroma
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from pathlib import Path
import openai
import os
import logging

logger = logging.getLogger(__name__)

def setup_rag_database(persist_directory: str = "rag_dataset/chroma/") -> None:
    """
    Set up the RAG database with Verilog designs from MG-Verilog dataset.
    
    Args:
        persist_directory: Directory to persist the ChromaDB
    """
    # Ensure persist directory exists
    persist_path = Path(persist_directory)
    persist_path.mkdir(parents=True, exist_ok=True)
    print(f"Using RAG database directory: {persist_path}")
    
    # Create embedding method
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
        
    embedding = OpenAIEmbeddings(api_key=api_key)
    openai.api_key = api_key

    print("Loading MG-Verilog dataset...")
    # Get dataset
    ds = load_dataset("GaTech-EIC/MG-Verilog")

    # Store summary and code for each script within dataset
    docs = []
    print("Processing dataset entries...")
    for i, row in enumerate(ds['train']):
        # Combine summary and code in a structured way
        content = f"""Summary: {row['description']['high_level_global_summary']}

Verilog Implementation:
{row['code']}"""
        
        docs.append(Document(
            page_content=content,
            metadata={
                "summary": row['description']['high_level_global_summary'],
                "module_name": row.get('module_name', 'unknown'),  # Store module name if available
                "category": row.get('category', 'unknown')  # Store category if available
            }
        ))
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1} entries...")

    print(f"Total entries to add: {len(docs)}")
    # Store data in chunks into chromadb
    vectordb = Chroma(
        embedding_function=embedding,
        persist_directory=str(persist_path)
    )
    
    print("Adding documents to ChromaDB...")
    # Add documents in batches of 100
    batch_size = 100
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        vectordb.add_documents(batch)
        print(f"Added batch {i//batch_size + 1} of {(len(docs) + batch_size - 1)//batch_size}")

    # Save chromadb
    num_docs = len(vectordb.get()["ids"])
    print(f"Total documents in ChromaDB: {num_docs}")
    vectordb.persist()
    print("ChromaDB setup complete!")

if __name__ == "__main__":
    # Use the directory where this script is located
    script_dir = Path(__file__).parent
    setup_rag_database(str(script_dir / "rag_dataset" / "chroma")) 