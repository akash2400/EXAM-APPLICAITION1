#!/usr/bin/env python3
"""
Simple template test to check for syntax errors
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jinja2 import Environment, FileSystemLoader

def test_template_syntax():
    """Test template syntax without Flask context."""
    
    print("🧪 Testing Template Syntax")
    print("=" * 50)
    
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates'))
    
    try:
        # Load the results template
        template = env.get_template('results.html')
        print("✅ Results template loaded successfully")
        
        # Test data
        test_data = {
            'exam': {'title': 'Test Exam'},
            'results': [
                {
                    'question': {'question_text': 'Test question', 'reference_answer': 'Test answer', 'max_marks': 10},
                    'student_answer': 'Student answer',
                    'llm_score': 8.5,
                    'llm_explanation': 'Good answer',
                    'final_marks': None,
                    'is_approved': False
                }
            ],
            'total_score': 0,
            'max_possible': 10,
            'all_approved': False
        }
        
        # Try to render with test data
        html = template.render(**test_data)
        print("✅ Template rendered successfully")
        print(f"   Output size: {len(html)} characters")
        
        # Check for common issues
        if 'undefined' in html.lower():
            print("⚠️  Warning: 'undefined' found in output")
        if 'error' in html.lower():
            print("⚠️  Warning: 'error' found in output")
            
        return True
        
    except Exception as e:
        print(f"❌ Template error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_template_syntax()
    sys.exit(0 if success else 1)

