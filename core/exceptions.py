"""
Custom exceptions for the RAG Master 1 application.
"""


class RAGException(Exception):
    """Base exception for RAG application."""
    pass


class ConfigurationError(RAGException):
    """Raised when configuration is invalid or missing."""
    pass


class IndexationError(RAGException):
    """Raised when there's an error during document indexation."""
    pass


class RetrievalError(RAGException):
    """Raised when there's an error during document retrieval."""
    pass


class EvaluationError(RAGException):
    """Raised when there's an error during evaluation."""
    pass


class CopilotError(RAGException):
    """Raised when there's an error with Copilot SDK."""
    pass
