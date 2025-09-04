#!/usr/bin/env python3
"""
Configuration file for Advanced AI Evaluator settings
"""

# CleanEvaluator Configuration
CACHE_DIR = "./adaptive_cache"  # Directory for model caching (matches CleanEvaluator)

# Logging Configuration
LOG_EVALUATIONS = True  # Log evaluation results for analysis
LOG_DETAILED_BREAKDOWN = True  # Log detailed breakdown for debugging

# Evaluator Selection Configuration
DEFAULT_EVALUATOR_TYPE = "optimized_sas"  # Options: "ai", "clean", "optimized_sas"

# Threshold Configuration for Fair Evaluation
EVALUATION_THRESHOLDS = {
    "pass_threshold": 2.5,  # Minimum score to pass (out of 5)
    "excellent_threshold": 4.0,  # Score for excellent performance
    "good_threshold": 3.0,  # Score for good performance
    "fair_threshold": 2.0,  # Score for fair performance
    "irrelevance_threshold": 0.15,  # Below this similarity = irrelevant
    "critical_word_penalty_threshold": 0.8,  # Above this = severe penalty
    "sas_threshold": 0.6,  # OptimizedSAS similarity threshold (0-1) - model-driven filtering
}

def get_evaluator_config():
    """Get the current evaluator configuration."""
    return {
        "cache_dir": CACHE_DIR,
        "log_evaluations": LOG_EVALUATIONS,
        "log_detailed_breakdown": LOG_DETAILED_BREAKDOWN,
        "default_evaluator_type": DEFAULT_EVALUATOR_TYPE,
        "evaluation_thresholds": EVALUATION_THRESHOLDS
    }

def update_config(**kwargs):
    """Update configuration settings."""
    global CACHE_DIR, LOG_EVALUATIONS, LOG_DETAILED_BREAKDOWN, DEFAULT_EVALUATOR_TYPE, EVALUATION_THRESHOLDS
    
    for key, value in kwargs.items():
        if key == "cache_dir":
            CACHE_DIR = value
        elif key == "log_evaluations":
            LOG_EVALUATIONS = value
        elif key == "log_detailed_breakdown":
            LOG_DETAILED_BREAKDOWN = value
        elif key == "default_evaluator_type":
            DEFAULT_EVALUATOR_TYPE = value
        elif key == "evaluation_thresholds":
            EVALUATION_THRESHOLDS.update(value)

def print_config():
    """Print current configuration."""
    config = get_evaluator_config()
    print("Current Evaluator Configuration:")
    print("=" * 40)
    for key, value in config.items():
        print(f"{key}: {value}")
    print("=" * 40)

if __name__ == "__main__":
    print_config()
