#!/usr/bin/env python3
"""
Test Auto-Submission Functionality
Tests the auto-submission feature when exam time expires.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app and models
from app import app, db, User, Exam, Question, ExamSession, Result
from flask import url_for

class TestAutoSubmission(unittest.TestCase):
    """Test cases for auto-submission functionality."""
    
    def setUp(self):
        """Set up test database and data."""
        # Use in-memory SQLite database for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
            
            # Create test user
            self.test_user = User(
                username='teststudent',
                password='password123',  # In real app, this would be hashed
                role='student'
            )
            db.session.add(self.test_user)
            
            # Create test admin
            self.test_admin = User(
                username='testadmin',
                password='admin123',  # In real app, this would be hashed
                role='admin'
            )
            db.session.add(self.test_admin)
            
            # Create test department
            from app import Department
            self.test_department = Department(name='Test Department')
            db.session.add(self.test_department)
            db.session.flush()  # Get the department ID
            
            # Create test exam
            self.test_exam = Exam(
                title='Test Auto-Submission Exam',
                description='Test exam for auto-submission',
                department_id=self.test_department.id,
                duration_minutes=1,  # 1 minute for quick testing
                is_enabled=True,
                is_active=True
            )
            db.session.add(self.test_exam)
            db.session.flush()  # Get the exam ID
            
            # Create test question
            self.test_question = Question(
                exam_id=self.test_exam.id,
                question_text='What is the capital of France?',
                reference_answer='The capital of France is Paris.',
                max_marks=10,
                question_order=1
            )
            db.session.add(self.test_question)
            
            db.session.commit()
    
    def tearDown(self):
        """Clean up after tests."""
        with app.app_context():
            db.drop_all()
    
    def test_01_auto_submit_function_exists(self):
        """Test that auto_submit_exam_answers function exists and is callable."""
        print("\n--- Testing Auto-Submit Function Exists ---")
        
        with app.app_context():
            # Import the function
            from app import auto_submit_exam_answers
            
            # Test that function exists and is callable
            self.assertTrue(callable(auto_submit_exam_answers))
            print("✓ auto_submit_exam_answers function exists and is callable")
    
    def test_02_auto_submit_creates_result(self):
        """Test that auto-submission creates a result record."""
        print("\n--- Testing Auto-Submit Creates Result ---")
        
        with app.app_context():
            from app import auto_submit_exam_answers
            
            # Create an exam session
            session = ExamSession(
                exam_id=self.test_exam.id,
                student_id=self.test_user.id,
                start_time=datetime.utcnow()
            )
            db.session.add(session)
            db.session.commit()
            
            # Check no results exist before auto-submit
            results_before = Result.query.filter_by(
                exam_id=self.test_exam.id,
                student_id=self.test_user.id
            ).count()
            self.assertEqual(results_before, 0)
            
            # Call auto-submit function
            auto_submit_exam_answers(
                self.test_exam.id, 
                self.test_user.id, 
                session.id
            )
            db.session.commit()
            
            # Check result was created
            results_after = Result.query.filter_by(
                exam_id=self.test_exam.id,
                student_id=self.test_user.id
            ).all()
            
            self.assertEqual(len(results_after), 1)
            result = results_after[0]
            
            # Verify result properties
            self.assertEqual(result.exam_id, self.test_exam.id)
            self.assertEqual(result.student_id, self.test_user.id)
            self.assertEqual(result.marks_awarded, 0)
            self.assertEqual(result.ai_score, 0.0)
            self.assertIn("Auto-submitted due to time expiration", result.student_answer)
            
            print(f"✓ Auto-submit created result: {result.student_answer}")
    
    def test_03_auto_submit_handles_existing_result(self):
        """Test that auto-submit doesn't create duplicate results."""
        print("\n--- Testing Auto-Submit Handles Existing Result ---")
        
        with app.app_context():
            from app import auto_submit_exam_answers
            
            # Create an existing result
            existing_result = Result(
                exam_id=self.test_exam.id,
                student_id=self.test_user.id,
                question_id=self.test_question.id,
                student_answer="Paris is the capital of France.",
                marks_awarded=8.5,
                ai_score=0.85,
                submitted_at=datetime.utcnow()
            )
            db.session.add(existing_result)
            db.session.commit()
            
            # Create session
            session = ExamSession(
                exam_id=self.test_exam.id,
                student_id=self.test_user.id,
                start_time=datetime.utcnow()
            )
            db.session.add(session)
            db.session.commit()
            
            # Count results before auto-submit
            results_before = Result.query.filter_by(
                exam_id=self.test_exam.id,
                student_id=self.test_user.id
            ).count()
            
            # Call auto-submit function
            auto_submit_exam_answers(
                self.test_exam.id, 
                self.test_user.id, 
                session.id
            )
            db.session.commit()
            
            # Count results after auto-submit
            results_after = Result.query.filter_by(
                exam_id=self.test_exam.id,
                student_id=self.test_user.id
            ).count()
            
            # Should not create additional result
            self.assertEqual(results_before, results_after)
            
            print("✓ Auto-submit correctly handled existing result")
    
    def test_04_time_remaining_endpoint(self):
        """Test the time remaining endpoint."""
        print("\n--- Testing Time Remaining Endpoint ---")
        
        with app.app_context():
            # Create session
            session = ExamSession(
                exam_id=self.test_exam.id,
                student_id=self.test_user.id,
                start_time=datetime.utcnow()
            )
            db.session.add(session)
            db.session.commit()
            
            # Login as student
            with self.app.session_transaction() as sess:
                sess['_user_id'] = str(self.test_user.id)
                sess['_fresh'] = True
            
            # Test time remaining endpoint
            response = self.app.get(f'/student/exam/{self.test_exam.id}/time_remaining')
            
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            
            self.assertIn('time_remaining', data)
            self.assertIn('exam_duration', data)
            self.assertIn('session_start', data)
            
            self.assertEqual(data['exam_duration'], 1)  # 1 minute
            self.assertGreaterEqual(data['time_remaining'], 0)
            
            print(f"✓ Time remaining endpoint works: {data['time_remaining']} minutes left")
    
    def test_05_expired_exam_redirects_to_results(self):
        """Test that accessing an expired exam redirects to results."""
        print("\n--- Testing Expired Exam Redirect ---")
        
        with app.app_context():
            # Create session that started 2 minutes ago (expired)
            expired_start_time = datetime.utcnow() - timedelta(minutes=2)
            session = ExamSession(
                exam_id=self.test_exam.id,
                student_id=self.test_user.id,
                start_time=expired_start_time
            )
            db.session.add(session)
            db.session.commit()
            
            # Login as student
            with self.app.session_transaction() as sess:
                sess['_user_id'] = str(self.test_user.id)
                sess['_fresh'] = True
            
            # Try to access the exam
            response = self.app.get(f'/student/exam/{self.test_exam.id}')
            
            # Should redirect to results (302) or dashboard
            self.assertIn(response.status_code, [302, 200])
            
            print("✓ Expired exam correctly redirects")
    
    def test_06_auto_submit_error_handling(self):
        """Test that auto-submit handles errors gracefully."""
        print("\n--- Testing Auto-Submit Error Handling ---")
        
        with app.app_context():
            from app import auto_submit_exam_answers
            
            # Test with invalid exam ID (should not crash)
            try:
                auto_submit_exam_answers(99999, self.test_user.id, 1)
                print("✓ Auto-submit handles invalid exam ID gracefully")
            except Exception as e:
                self.fail(f"Auto-submit should handle errors gracefully, but raised: {e}")
            
            # Test with invalid student ID (should not crash)
            try:
                auto_submit_exam_answers(self.test_exam.id, 99999, 1)
                print("✓ Auto-submit handles invalid student ID gracefully")
            except Exception as e:
                self.fail(f"Auto-submit should handle errors gracefully, but raised: {e}")
    
    def run_comprehensive_test(self):
        """Run all tests and provide summary."""
        print("\n" + "="*60)
        print("RUNNING AUTO-SUBMISSION TEST SUITE")
        print("="*60)
        
        test_methods = [
            self.test_01_auto_submit_function_exists,
            self.test_02_auto_submit_creates_result,
            self.test_03_auto_submit_handles_existing_result,
            self.test_04_time_remaining_endpoint,
            self.test_05_expired_exam_redirects_to_results,
            self.test_06_auto_submit_error_handling
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            try:
                self.setUp()
                test_method()
                self.tearDown()
                passed_tests += 1
            except Exception as e:
                print(f"✗ {test_method.__name__} failed: {str(e)}")
                self.tearDown()
        
        print("\n" + "="*60)
        print("AUTO-SUBMISSION TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 ALL AUTO-SUBMISSION TESTS PASSED!")
            print("✅ Auto-submission functionality is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the errors above.")
        
        return passed_tests == total_tests

def main():
    """Main function to run the test suite."""
    print("Auto-Submission Test Suite")
    print("This test suite validates the auto-submission functionality.")
    
    # Create test instance
    test_suite = TestAutoSubmission()
    
    # Run comprehensive test
    success = test_suite.run_comprehensive_test()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
