#!/usr/bin/env python3
"""
Configuration file for LLM Evaluator settings
"""

# LLM Evaluator Configuration
OLLAMA_URL = "http://localhost:11434"  # Ollama server URL
MODEL_NAME = "llama2:latest"  # Model to use for evaluation
MAX_RETRIES = 3  # Maximum retries for API calls
TIMEOUT = 60  # Timeout for API calls in seconds
SAS_THRESHOLD = 0.15  # SAS similarity threshold for quality filtering

# Logging Configuration
LOG_EVALUATIONS = True  # Log evaluation results for analysis
LOG_DETAILED_BREAKDOWN = True  # Log detailed breakdown for debugging

# Evaluator Selection Configuration
DEFAULT_EVALUATOR_TYPE = "llm"  # Only LLM evaluator supported

# Threshold Configuration for Fair Evaluation
EVALUATION_THRESHOLDS = {
    "pass_threshold": 2.5,  # Minimum score to pass (out of 5)
    "excellent_threshold": 4.0,  # Score for excellent performance
    "good_threshold": 3.0,  # Score for good performance
    "fair_threshold": 2.0,  # Score for fair performance
    "sas_threshold": 0.15,  # SAS similarity threshold for quality filtering
}

def get_evaluator_config():
    """Get the current evaluator configuration."""
    return {
        "ollama_url": OLLAMA_URL,
        "model_name": MODEL_NAME,
        "max_retries": MAX_RETRIES,
        "timeout": TIMEOUT,
        "sas_threshold": SAS_THRESHOLD,
        "log_evaluations": LOG_EVALUATIONS,
        "log_detailed_breakdown": LOG_DETAILED_BREAKDOWN,
        "default_evaluator_type": DEFAULT_EVALUATOR_TYPE,
        "evaluation_thresholds": EVALUATION_THRESHOLDS
    }

def update_config(**kwargs):
    """Update configuration settings."""
    global OLLAMA_URL, MODEL_NAME, MAX_RETRIES, TIMEOUT, SAS_THRESHOLD, LOG_EVALUATIONS, LOG_DETAILED_BREAKDOWN, DEFAULT_EVALUATOR_TYPE, EVALUATION_THRESHOLDS
    
    for key, value in kwargs.items():
        if key == "ollama_url":
            OLLAMA_URL = value
        elif key == "model_name":
            MODEL_NAME = value
        elif key == "max_retries":
            MAX_RETRIES = value
        elif key == "timeout":
            TIMEOUT = value
        elif key == "sas_threshold":
            SAS_THRESHOLD = value
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
