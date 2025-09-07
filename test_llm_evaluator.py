#!/usr/bin/env python3
"""
Test script for LLM Evaluator
=============================

This script tests the LLM evaluator functionality to ensure it works correctly
with Ollama and the Llama 7B model.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_evaluator import LLMEvaluator
import json

def test_llm_evaluator():
    """Test the LLM evaluator with sample questions."""
    
    print("🧪 Testing LLM Evaluator")
    print("=" * 50)
    
    # Initialize evaluator
    print("1. Initializing LLM Evaluator...")
    evaluator = LLMEvaluator()
    
    if not evaluator.is_available:
        print("❌ LLM Evaluator is not available!")
        print("Please ensure:")
        print("   - Ollama is installed and running")
        print("   - Run: ollama serve")
        print("   - Run: ollama pull llama2:7b")
        return False
    
    print("✅ LLM Evaluator initialized successfully")
    print(f"   Model: {evaluator.model_name}")
    print(f"   URL: {evaluator.ollama_url}")
    
    # Test evaluation
    print("\n2. Testing evaluation...")
    
    test_cases = [
        {
            "question": "What is photosynthesis?",
            "reference_answer": "Photosynthesis is the process by which plants convert light energy into chemical energy, using carbon dioxide and water to produce glucose and oxygen.",
            "student_answer": "Photosynthesis is how plants make food using sunlight, water, and carbon dioxide.",
            "max_marks": 10
        },
        {
            "question": "Explain the water cycle.",
            "reference_answer": "The water cycle is the continuous movement of water through evaporation, condensation, and precipitation processes.",
            "student_answer": "Water evaporates from oceans, forms clouds, and falls as rain.",
            "max_marks": 8
        },
        {
            "question": "What is the capital of France?",
            "reference_answer": "The capital of France is Paris.",
            "student_answer": "Paris is the capital city of France.",
            "max_marks": 5
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Test Case {i}:")
        print(f"   Question: {test_case['question']}")
        print(f"   Student Answer: {test_case['student_answer']}")
        
        result = evaluator.evaluate(
            student_answer=test_case['student_answer'],
            reference_answer=test_case['reference_answer'],
            question=test_case['question'],
            max_marks=test_case['max_marks']
        )
        
        if result['details']['status'] == 'evaluated':
            print(f"   ✅ LLM Score: {result['final_score']:.1f}/{test_case['max_marks']}")
            print(f"   💭 Explanation: {result['details']['explanation']}")
        else:
            print(f"   ❌ Evaluation failed: {result['details'].get('error', 'Unknown error')}")
    
    # Test model info
    print("\n3. Model Information:")
    model_info = evaluator.get_model_info()
    print(json.dumps(model_info, indent=2))
    
    print("\n✅ All tests completed!")
    return True

if __name__ == "__main__":
    success = test_llm_evaluator()
    sys.exit(0 if success else 1)
