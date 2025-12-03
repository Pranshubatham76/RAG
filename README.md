# Discourse Q&A Assistant with RAG

A Retrieval-Augmented Generation (RAG) web application that helps students and instructors get answers from a Discourse forum using OpenAI-compatible models via AIPIPE.

## 🎯 Problem Statement

This application fetches and indexes data from a Discourse forum, implements a RAG pipeline where a retriever fetches relevant posts and a generator (LLM) answers user queries using those retrieved posts as context.

## ✨ Features

- **Data Fetching**: Fetch posts from Discourse forums programmatically
- **RAG Pipeline**: Retrieval-Augmented Generation using vector search + LLM
- **Vector Storage**: Support for ChromaDB and FAISS vector stores
- **LLM Integration**: OpenAI-compatible models via AIPIPE proxy to OpenRouter
- **REST API**: Clean backend API with health checks and Q&A endpoints
- **Web Interface**: User-friendly frontend for asking questions
- **Chunking**: Intelligent text chunking for optimal retrieval
- **Embeddings**: Local SentenceTransformers or remote embeddings support

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Discourse     │───▶│   Ingestion     │───▶│   Vector Store   │
│   Forum API     │    │   Pipeline      │    │   (Chroma/FAISS) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐             │
│   Frontend      │◀──▶│   Backend API   │◀────────────┘
│   (React/Vue)   │    │   (Django)      │
└─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   AIPIPE        │
                       │   (OpenRouter)  │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
