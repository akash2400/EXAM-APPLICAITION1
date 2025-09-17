#!/usr/bin/env python3
"""
Evaluator Selector for LLM Evaluator
====================================

This module provides a unified interface for the LLM evaluator system.
Currently supports:
- LLMEvaluator: LLM-based evaluation using Ollama and Llama 7B
"""

import logging
from typing import Optional
from llm_evaluator import LLMEvaluator
from evaluator_config import get_evaluator_config

logger = logging.getLogger(__name__)

def get_evaluator_from_config(evaluator_type: str = "llm") -> LLMEvaluator:
    """
    Get the LLM evaluator from configuration.
    
    Args:
        evaluator_type (str): Type of evaluator (only "llm" supported)
        
    Returns:
        LLMEvaluator: Initialized LLM evaluator instance
    """
    config = get_evaluator_config()
    
    logger.info("Initializing LLMEvaluator as main evaluation engine")
    return _initialize_llm_evaluator(config)

def _initialize_llm_evaluator(config: dict) -> LLMEvaluator:
    """
    Initialize the LLMEvaluator as the main evaluation engine.
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        LLMEvaluator: Initialized evaluator instance
    """
    try:
        logger.info("Initializing LLMEvaluator...")
        
        # Get configuration values
        ollama_url = config.get('ollama_url', 'http://localhost:11434')
        model_name = config.get('model_name', 'llama2:latest')
        max_retries = config.get('max_retries', 3)
        timeout = config.get('timeout', 60)
        sas_threshold = config.get('sas_threshold', 0.15)
        
        evaluator = LLMEvaluator(
            ollama_url=ollama_url,
            model_name=model_name,
            max_retries=max_retries,
            timeout=timeout,
            sas_threshold=sas_threshold
        )
        
        logger.info("LLMEvaluator initialized successfully")
        return evaluator
            
    except Exception as e:
        logger.error(f"Error initializing LLMEvaluator: {e}")
        raise

def get_evaluator_info(evaluator_type: str = "llm") -> dict:
    """
    Get information about the current evaluator.
    
    Args:
        evaluator_type (str): Type of evaluator (only "llm" supported)
        
    Returns:
        dict: Evaluator information
    """
    try:
        evaluator = get_evaluator_from_config(evaluator_type)
        
        return {
            'type': 'LLMEvaluator',
            'status': 'initialized' if evaluator.is_available else 'not_available',
            'model_name': evaluator.model_name,
            'ollama_url': evaluator.ollama_url,
            'is_available': evaluator.is_available,
            'config': {
                'model_name': evaluator.model_name,
                'ollama_url': evaluator.ollama_url,
                'max_retries': evaluator.max_retries,
                'timeout': evaluator.timeout,
                'filter_threshold': evaluator.filter_threshold
            }
        }
    except Exception as e:
        return {
            'type': 'LLMEvaluator',
            'status': 'error',
            'error': str(e)
        }