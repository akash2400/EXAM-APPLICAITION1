#!/usr/bin/env python3
"""
Test script for results template
===============================

This script tests the results template to ensure it renders correctly
without any template errors.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template
from datetime import datetime

# Create a test Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'
app.config['SERVER_NAME'] = 'localhost:5002'
app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'http'

# Mock data for testing
class MockExam:
    def __init__(self):
        self.id = 1
        self.title = "Test Exam - LLM Evaluation"

class MockQuestion:
    def __init__(self, id, text, answer, max_marks):
        self.id = id
        self.question_text = text
        self.reference_answer = answer
        self.max_marks = max_marks

class MockResult:
    def __init__(self, question, student_answer, llm_score, llm_explanation, final_marks=None, is_approved=False):
        self.question = question
        self.student_answer = student_answer
        self.llm_score = llm_score
        self.llm_explanation = llm_explanation
        self.final_marks = final_marks
        self.is_approved = is_approved
        self.submitted_at = datetime.now()

def test_results_template():
    """Test the results template with mock data."""
    
    print("🧪 Testing Results Template")
    print("=" * 50)
    
    # Create mock data
    exam = MockExam()
    
    questions = [
        MockQuestion(1, "What is photosynthesis?", 
                    "Photosynthesis is the process by which plants convert light energy into chemical energy.", 10),
        MockQuestion(2, "Explain the water cycle.", 
                    "The water cycle is the continuous movement of water through evaporation, condensation, and precipitation.", 8),
        MockQuestion(3, "What is the capital of France?", 
                    "The capital of France is Paris.", 5)
    ]
    
    # Test case 1: Pending results (not approved)
    print("\n1. Testing pending results (not approved)...")
    pending_results = [
        MockResult(questions[0], "Plants make food using sunlight and water.", 7.5, "Good understanding but missing some details.", is_approved=False),
        MockResult(questions[1], "Water evaporates, forms clouds, and falls as rain.", 6.0, "Basic understanding but incomplete explanation.", is_approved=False),
        MockResult(questions[2], "Paris is the capital of France.", 5.0, "Correct and complete answer.", is_approved=False)
    ]
    
    try:
        with app.app_context():
            # Test pending results
            html = render_template('results.html',
                                 exam=exam,
                                 results=pending_results,
                                 total_score=0,
                                 max_possible=23,
                                 all_approved=False)
            print("✅ Pending results template rendered successfully")
            print(f"   Template size: {len(html)} characters")
            
    except Exception as e:
        print(f"❌ Error rendering pending results: {str(e)}")
        return False
    
    # Test case 2: Approved results
    print("\n2. Testing approved results...")
    approved_results = [
        MockResult(questions[0], "Plants make food using sunlight and water.", 7.5, "Good understanding but missing some details.", final_marks=7.5, is_approved=True),
        MockResult(questions[1], "Water evaporates, forms clouds, and falls as rain.", 6.0, "Basic understanding but incomplete explanation.", final_marks=6.0, is_approved=True),
        MockResult(questions[2], "Paris is the capital of France.", 5.0, "Correct and complete answer.", final_marks=5.0, is_approved=True)
    ]
    
    try:
        with app.app_context():
            # Test approved results
            html = render_template('results.html',
                                 exam=exam,
                                 results=approved_results,
                                 total_score=18.5,
                                 max_possible=23,
                                 all_approved=True)
            print("✅ Approved results template rendered successfully")
            print(f"   Template size: {len(html)} characters")
            
    except Exception as e:
        print(f"❌ Error rendering approved results: {str(e)}")
        return False
    
    # Test case 3: Edge cases
    print("\n3. Testing edge cases...")
    
    # Empty results
    try:
        with app.app_context():
            html = render_template('results.html',
                                 exam=exam,
                                 results=[],
                                 total_score=0,
                                 max_possible=0,
                                 all_approved=True)
            print("✅ Empty results template rendered successfully")
    except Exception as e:
        print(f"❌ Error rendering empty results: {str(e)}")
        return False
    
    # Results with None values
    edge_results = [
        MockResult(questions[0], "", None, "No answer provided.", final_marks=None, is_approved=False)
    ]
    
    try:
        with app.app_context():
            html = render_template('results.html',
                                 exam=exam,
                                 results=edge_results,
                                 total_score=0,
                                 max_possible=10,
                                 all_approved=False)
            print("✅ Edge case results template rendered successfully")
    except Exception as e:
        print(f"❌ Error rendering edge case results: {str(e)}")
        return False
    
    print("\n✅ All template tests passed!")
    return True

if __name__ == "__main__":
    success = test_results_template()
    sys.exit(0 if success else 1)
