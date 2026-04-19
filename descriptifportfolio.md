# RAG Master 1 — AI Teaching Assistant

## Tagline
Full-stack RAG assistant with hybrid search, Copilot learning tools, and MCP integrations for university students.

## Description
A comprehensive AI teaching assistant for Master 1 CS students featuring hybrid search (BM25 + semantic), Copilot-powered learning tools (quiz generation, flashcards, mind maps), and MCP integrations (YouTube, Gmail, Arxiv, Wikipedia, Notion). Includes a 200-question automated evaluation benchmark and incremental re-indexing with change detection.

## Motivation
Students deserve answers grounded in their actual course material — not generic web content. This RAG system adapts to different learning styles with tools for quizzes, flashcards, and visual mind maps.

## Tech Stack
- **Backend**: Python, Flask, LangChain
- **Frontend**: React, Vite
- **AI/ML**: OpenAI GPT-4o-mini, ChromaDB, BM25
- **Integrations**: GitHub Copilot SDK, MCP (YouTube, Brave, Arxiv, Wikipedia, Gmail, Drive, Notion)
- **Evaluation**: 200-question benchmark pipeline

## Key Features
- Hybrid search pipeline: query rewriting → BM25 + semantic → re-ranking → LLM answer
- Copilot Tools: quiz generation, flashcards, mind maps, charts, concept extraction
- MCP servers: YouTube Transcript, Brave Search, Arxiv, Wikipedia, Gmail, Google Drive, Notion
- Automated evaluation with 200-question benchmark
- Incremental and forced re-indexing with change detection

## Skills Demonstrated
- Hybrid search architecture (BM25 + semantic + reranking)
- MCP (Model Context Protocol) integrations
- Evaluation pipeline design for RAG systems
- Copilot SDK extension development
- Full-stack AI application development

## Category
`AI/ML` · `RAG` · `EdTech` · `MCP` · `Full-Stack`

## Status
In Progress

## Complexity
⭐⭐⭐⭐⭐ Advanced

## Links
- GitHub: https://github.com/yanimohellebi26/RAG-Master1
