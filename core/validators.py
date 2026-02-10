"""
Input validation utilities for the RAG application.
"""

import re
from typing import Any

from core.constants import (
    MAX_QUESTION_LENGTH,
    MIN_QUESTION_LENGTH,
    MIN_NB_SOURCES,
    MAX_NB_SOURCES,
    SUSPICIOUS_PATTERNS,
)


def validate_question(question: str, max_length: int = MAX_QUESTION_LENGTH) -> tuple[bool, str]:
    """
    Validate user question input.
    
    Args:
        question: The question to validate
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not question:
        return False, "Question vide"
    
    if not isinstance(question, str):
        return False, "Question doit être une chaîne de caractères"
    
    question = question.strip()
    
    if len(question) < MIN_QUESTION_LENGTH:
        return False, f"Question trop courte (minimum {MIN_QUESTION_LENGTH} caractères)"
    
    if len(question) > max_length:
        return False, f"Question trop longue (maximum {max_length} caractères)"
    
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            return False, "Question contient des caractères suspects"
    
    return True, ""


def validate_subjects(subjects: list[str], allowed_subjects: list[str]) -> tuple[bool, str]:
    """
    Validate subject filter list.
    
    Args:
        subjects: List of subjects to validate
        allowed_subjects: List of valid subject names
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(subjects, list):
        return False, "Sujets doit être une liste"
    
    for subject in subjects:
        if not isinstance(subject, str):
            return False, "Chaque sujet doit être une chaîne de caractères"
        if subject not in allowed_subjects:
            return False, f"Sujet invalide: {subject}"
    
    return True, ""


def validate_nb_sources(nb_sources: Any) -> tuple[bool, str]:
    """
    Validate number of sources to retrieve.
    
    Args:
        nb_sources: Number of sources
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        nb = int(nb_sources)
    except (TypeError, ValueError):
        return False, "Nombre de sources doit être un entier"
    
    if nb < MIN_NB_SOURCES:
        return False, f"Nombre de sources doit être au moins {MIN_NB_SOURCES}"
    
    if nb > MAX_NB_SOURCES:
        return False, f"Nombre de sources maximum: {MAX_NB_SOURCES}"
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove any path separators
    filename = filename.replace("/", "").replace("\\", "")
    # Remove any parent directory references
    filename = filename.replace("..", "")
    # Remove any null bytes
    filename = filename.replace("\x00", "")
    
    return filename
