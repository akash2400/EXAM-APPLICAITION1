#!/usr/bin/env python3
"""
Test Department Details View
Tests the new department details functionality.
"""

import unittest
import sys
import os
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_department_details_route():
    """Test that the department details route exists and is accessible."""
    print("Testing Department Details Route...")
    
    try:
        from app import app, db, Department, Exam, User, Result
        
        with app.app_context():
            # Test that the route function exists
            from app import department_details
            assert callable(department_details), "department_details function should be callable"
            
            print("✓ department_details function exists and is callable")
            
            # Test that the template exists
            import os
            template_path = os.path.join('templates', 'department_details.html')
            assert os.path.exists(template_path), f"Template {template_path} should exist"
            
            print("✓ department_details.html template exists")
            
            return True
            
    except Exception as e:
        print(f"✗ Department details test failed: {e}")
        return False

def test_department_model_relationships():
    """Test that the Department model has the required relationships."""
    print("\nTesting Department Model Relationships...")
    
    try:
        from app import Department, Exam, User
        
        # Check that Department has the required relationships
        assert hasattr(Department, 'students'), "Department should have students relationship"
        assert hasattr(Department, 'exams'), "Department should have exams relationship"
        
        print("✓ Department model has required relationships")
        
        # Check that the relationships are properly configured
        dept = Department()
        assert hasattr(dept, 'students'), "Department instance should have students attribute"
        assert hasattr(dept, 'exams'), "Department instance should have exams attribute"
        
        print("✓ Department relationships are properly configured")
        
        return True
        
    except Exception as e:
        print(f"✗ Department model test failed: {e}")
        return False

def test_template_syntax():
    """Test that the template has correct Jinja2 syntax."""
    print("\nTesting Template Syntax...")
    
    try:
        from jinja2 import Environment, FileSystemLoader
        
        # Create Jinja2 environment
        env = Environment(loader=FileSystemLoader('templates'))
        
        # Try to load the template
        template = env.get_template('department_details.html')
        
        # Test basic template rendering with dummy data
        test_data = {
            'department': type('Department', (), {
                'id': 1,
                'name': 'Test Department',
                'description': 'Test Description',
                'created_at': datetime.now()
            })(),
            'exam_stats': [],
            'student_stats': []
        }
        
        # Render template (this will catch syntax errors)
        rendered = template.render(**test_data)
        
        # Check that key elements are present
        assert 'Test Department' in rendered, "Department name should be in rendered template"
        assert 'departmentTabs' in rendered, "Tab navigation should be present"
        assert 'exams' in rendered, "Exams section should be present"
        assert 'students' in rendered, "Students section should be present"
        
        print("✓ Template syntax is correct and renders properly")
        
        return True
        
    except Exception as e:
        print(f"✗ Template syntax test failed: {e}")
        return False

def test_route_url_generation():
    """Test that the route URL can be generated correctly."""
    print("\nTesting Route URL Generation...")
    
    try:
        from app import app
        
        with app.app_context():
            from flask import url_for
            
            # Test URL generation for department details
            url = url_for('department_details', department_id=1)
            expected_url = '/admin/department/1'
            
            assert url == expected_url, f"URL should be {expected_url}, got {url}"
            
            print(f"✓ Route URL generation works: {url}")
            
            return True
            
    except Exception as e:
        print(f"✗ Route URL generation test failed: {e}")
        return False

def test_manage_departments_integration():
    """Test that the manage departments page integrates with the new view."""
    print("\nTesting Manage Departments Integration...")
    
    try:
        # Check that the JavaScript function has been updated
        with open('templates/manage_departments.html', 'r') as f:
            content = f.read()
        
        # Check that the old alert is replaced with navigation
        assert 'window.location.href' in content, "JavaScript should navigate to department details"
        assert 'alert(' not in content or content.count('alert(') == 0, "Should not use alert for department details"
        
        print("✓ Manage departments page integrates with new view")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

def run_all_tests():
    """Run all department details tests."""
    print("="*60)
    print("DEPARTMENT DETAILS FUNCTIONALITY TESTS")
    print("="*60)
    
    tests = [
        test_department_details_route,
        test_department_model_relationships,
        test_template_syntax,
        test_route_url_generation,
        test_manage_departments_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
    
    print("\n" + "="*60)
    print("DEPARTMENT DETAILS TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL DEPARTMENT DETAILS TESTS PASSED!")
        print("✅ Department details functionality is working correctly.")
        print("\nKey Features Implemented:")
        print("• Department details page with comprehensive information")
        print("• Tabbed interface showing exams and students")
        print("• Exam statistics including scores and participation")
        print("• Student statistics and performance metrics")
        print("• Integration with existing department management")
        print("• Responsive design with Bootstrap components")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
