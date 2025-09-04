#!/usr/bin/env python3
"""
Evaluator Selector for Multiple AI Evaluators
============================================

This module provides a unified interface for selecting and initializing
different AI evaluators. Currently supports:
- AIEvaluator (default): Multi-layer evaluation with bi-encoder + cross-encoder
- CleanEvaluator: Enhanced evaluation with multiple AI models
- ModelBasedCriticalWordEvaluator: Model-based critical word detection with attention mechanisms
"""

import logging
from typing import Optional, Union
from ai_evaluator import AIEvaluator, EvaluatorConfig
from optimized_sas_evaluator import OptimizedSASEvaluator
from evaluator_config import get_evaluator_config

# Try to import optional evaluators
try:
    from clean_model_driven_evaluator import CleanEvaluator
    CLEAN_EVALUATOR_AVAILABLE = True
except ImportError:
    CleanEvaluator = None
    CLEAN_EVALUATOR_AVAILABLE = False

logger = logging.getLogger(__name__)

def get_evaluator_from_config(evaluator_type: str = "ai") -> Union[AIEvaluator, CleanEvaluator, OptimizedSASEvaluator]:
    """
    Get the specified evaluator from configuration.
    
    Args:
        evaluator_type (str): Type of evaluator ("ai", "clean", "optimized_sas")
        
    Returns:
        Union[AIEvaluator, CleanEvaluator, OptimizedSASEvaluator]: Initialized evaluator instance
    """
    config = get_evaluator_config()
    cache_dir = config.get('cache_dir', './adaptive_cache')
    
    if evaluator_type.lower() == "ai":
        logger.info("Initializing AIEvaluator as main evaluation engine")
        return _initialize_ai_evaluator(cache_dir)
    elif evaluator_type.lower() == "optimized_sas":
        logger.info("Initializing OptimizedSASEvaluator as main evaluation engine")
        return _initialize_optimized_sas_evaluator(config)
    elif evaluator_type.lower() == "clean" and CLEAN_EVALUATOR_AVAILABLE:
        logger.info("Initializing CleanEvaluator as main evaluation engine")
        return _initialize_clean_evaluator(cache_dir)
    else:
        logger.info("Falling back to AIEvaluator as main evaluation engine")
        return _initialize_ai_evaluator(cache_dir)

def _initialize_ai_evaluator(cache_dir: str) -> AIEvaluator:
    """
    Initialize the AIEvaluator as the main evaluation engine.
    
    Args:
        cache_dir (str): Directory for model caching
        
    Returns:
        AIEvaluator: Initialized evaluator instance
    """
    try:
        logger.info("Initializing AIEvaluator (Multi-Layer)...")
        
        # Configure AIEvaluator with cache directory
        evaluator_config = EvaluatorConfig(cache_dir=cache_dir)
        evaluator = AIEvaluator(evaluator_config)
        
        logger.info("AIEvaluator initialized successfully")
        return evaluator
            
    except Exception as e:
        logger.error(f"Error initializing AIEvaluator: {e}")
        raise

def _initialize_clean_evaluator(cache_dir: str):
    """
    Initialize the CleanEvaluator as the main evaluation engine.
    
    Args:
        cache_dir (str): Directory for model caching
        
    Returns:
        CleanEvaluator: Initialized evaluator instance
    """
    if not CLEAN_EVALUATOR_AVAILABLE:
        raise ImportError("CleanEvaluator is not available")
        
    try:
        logger.info("Initializing CleanEvaluator...")
        
        evaluator = CleanEvaluator()
        evaluator.config.cache_dir = cache_dir
        
        if evaluator.initialize():
            logger.info("CleanEvaluator initialized successfully")
            return evaluator
        else:
            logger.error("Failed to initialize CleanEvaluator")
            raise RuntimeError("Failed to initialize CleanEvaluator")
            
    except Exception as e:
        logger.error(f"Error initializing CleanEvaluator: {e}")
        raise

def _initialize_optimized_sas_evaluator(config: dict) -> OptimizedSASEvaluator:
    """
    Initialize the OptimizedSASEvaluator as the main evaluation engine.
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        OptimizedSASEvaluator: Initialized evaluator instance
    """
    try:
        logger.info("Initializing OptimizedSASEvaluator...")
        
        # Get threshold from config
        thresholds = config.get('evaluation_thresholds', {})
        sas_threshold = thresholds.get('sas_threshold', 0.25)
        
        evaluator = OptimizedSASEvaluator(
            device="cpu",  # Use CPU by default for compatibility
            threshold=sas_threshold,
            max_marks=10  # Use 10 for compatibility with existing system
        )
        
        logger.info("OptimizedSASEvaluator initialized successfully")
        return evaluator
            
    except Exception as e:
        logger.error(f"Error initializing OptimizedSASEvaluator: {e}")
        raise

def get_evaluator_info(evaluator_type: str = "ai") -> dict:
    """
    Get information about the current evaluator.
    
    Args:
        evaluator_type (str): Type of evaluator ("ai", "clean", or "critical_word")
        
    Returns:
        dict: Evaluator information
    """
    try:
        evaluator = get_evaluator_from_config(evaluator_type)
        
        if isinstance(evaluator, AIEvaluator):
            return {
                'type': 'AIEvaluator',
                'status': 'initialized',
                'models': ['bi_encoder', 'cross_encoder'],
                'config': {
                    'cache_dir': evaluator.config.cache_dir,
                    'bi_encoder': evaluator.config.bi_encoder_name,
                    'cross_encoder': evaluator.config.cross_encoder_name
                }
            }
        elif isinstance(evaluator, OptimizedSASEvaluator):
            return {
                'type': 'OptimizedSASEvaluator',
                'status': 'initialized' if evaluator.model is not None else 'not_initialized',
                'models': [evaluator.model_name] if evaluator.model else [],
                'config': {
                    'model_name': evaluator.model_name,
                    'threshold': evaluator.threshold,
                    'max_marks': evaluator.max_marks,
                    'batch_size': evaluator.batch_size,
                    'device': evaluator.device
                }
            }
        else:
            return {
                'type': 'CleanEvaluator',
                'status': 'initialized' if evaluator.is_initialized else 'not_initialized',
                'models': list(evaluator.models.keys()) if hasattr(evaluator, 'models') else [],
                'config': {
                    'cache_dir': evaluator.config.cache_dir
                }
            }
    except Exception as e:
        return {
            'type': 'Unknown',
            'status': 'error',
            'error': str(e)
        }

