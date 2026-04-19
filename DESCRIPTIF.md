# RAG-Master1 — AI Teaching Assistant for Computer Science

## Description

A full-stack RAG (Retrieval-Augmented Generation) assistant built specifically for Master 1 Computer Science students at the University of Burgundy. Ask it anything covered in your courses — it retrieves relevant lecture notes, answers in natural language, and shows you exactly which sources it used.

## What it brings

Lecture slide search is slow and keyword-dependent; this assistant understands intent. Students can ask questions the way they think ("I don't understand why merge sort is O(n log n)") and get answers grounded in their actual course material — not generic web content. The Copilot Tools panel turns any answer into a quiz, flashcards, a mind map, or a data chart, adapting the content to different learning styles.

## How it works

Documents are chunked, embedded, and stored in a vector database. Incoming questions are rewritten for clarity, then retrieved via hybrid search combining BM25 keyword matching with semantic vector similarity. A re-ranker selects the most relevant chunks, which are injected into the LLM prompt alongside the conversation history. MCP servers extend the system's knowledge base with YouTube transcripts and external search results. An automated evaluation pipeline measures answer quality against a benchmark of 200 course questions.

## Status

✅ Core RAG pipeline complete and evaluated — MCP integrations actively expanding.

## Tech Stack

`Python` · `FastAPI` · `React` · `OpenAI API` · `ChromaDB` · `BM25` · `GitHub Copilot SDK` · `MCP` · `Qdrant`
