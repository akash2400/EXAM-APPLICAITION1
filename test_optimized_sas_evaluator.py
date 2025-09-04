#!/usr/bin/env python3
"""
Comprehensive Test Suite for OptimizedSASEvaluator
Tests all functionality including edge cases, different thresholds, and batch evaluation.
"""

import unittest
import sys
import os
from typing import Dict, Any

# Add the current directory to the path to import the evaluator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from optimized_sas_evaluator import OptimizedSASEvaluator

class TestOptimizedSASEvaluator(unittest.TestCase):
    """Test cases for OptimizedSASEvaluator class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with evaluator instance."""
        print("\n" + "="*60)
        print("INITIALIZING OPTIMIZED SAS EVALUATOR TEST SUITE")
        print("="*60)
        
        # Initialize evaluator with default settings
        cls.evaluator = OptimizedSASEvaluator(device="cpu", threshold=0.6, max_marks=10)
        
        # Test data for various scenarios
        cls.test_data = {
            'exact_match': {
                'student': "The capital of France is Paris.",
                'reference': "The capital of France is Paris.",
                'expected_category': 'Excellent'
            },
            'semantic_similar': {
                'student': "Paris serves as the capital city of France.",
                'reference': "The capital of France is Paris.",
                'expected_category': 'Excellent'
            },
            'partial_match': {
                'student': "France has a capital city.",
                'reference': "The capital of France is Paris.",
                'expected_category': 'Good'
            },
            'different_topic': {
                'student': "The weather is sunny today.",
                'reference': "The capital of France is Paris.",
                'expected_category': 'Filtered (Irrelevant)'
            },
            'empty_answer': {
                'student': "",
                'reference': "The capital of France is Paris.",
                'expected_category': 'Filtered'
            },
            'whitespace_only': {
                'student': "   \n\t  ",
                'reference': "The capital of France is Paris.",
                'expected_category': 'Filtered'
            },
            'complex_question': {
                'student': "Photosynthesis is the process where plants use sunlight, water, and carbon dioxide to produce glucose and oxygen.",
                'reference': "Photosynthesis is a process in which plants convert light energy into chemical energy, producing glucose and releasing oxygen.",
                'expected_category': 'Excellent'
            }
        }
    
    def test_01_initialization(self):
        """Test evaluator initialization."""
        print("\n--- Testing Initialization ---")
        
        # Test default initialization
        evaluator = OptimizedSASEvaluator()
        self.assertIsNotNone(evaluator.model)
        self.assertEqual(evaluator.threshold, 0.6)
        self.assertEqual(evaluator.max_marks, 10)
        self.assertEqual(evaluator.device, "cpu")
        
        # Test custom initialization
        custom_evaluator = OptimizedSASEvaluator(threshold=0.8, max_marks=20)
        self.assertEqual(custom_evaluator.threshold, 0.8)
        self.assertEqual(custom_evaluator.max_marks, 20)
        
        print("✓ Initialization tests passed")
    
    def test_02_threshold_update(self):
        """Test threshold update functionality."""
        print("\n--- Testing Threshold Update ---")
        
        original_threshold = self.evaluator.threshold
        new_threshold = 0.8
        
        self.evaluator.set_threshold(new_threshold)
        self.assertEqual(self.evaluator.threshold, new_threshold)
        
        # Reset to original
        self.evaluator.set_threshold(original_threshold)
        self.assertEqual(self.evaluator.threshold, original_threshold)
        
        print("✓ Threshold update tests passed")
    
    def test_03_exact_match_evaluation(self):
        """Test evaluation with exact matches."""
        print("\n--- Testing Exact Match Evaluation ---")
        
        data = self.test_data['exact_match']
        result = self.evaluator.evaluate(data['student'], data['reference'])
        
        # Verify result structure
        self.assertIn('final_score', result)
        self.assertIn('details', result)
        self.assertIn('raw_score', result['details'])
        self.assertIn('category', result['details'])
        
        # Exact match should have high score
        self.assertGreater(result['details']['raw_score'], 0.8)
        self.assertGreater(result['final_score'], 0)
        self.assertFalse(result['details']['filtered'])
        
        print(f"✓ Exact match: Raw score = {result['details']['raw_score']:.4f}, "
              f"Final score = {result['final_score']:.2f}")
    
    def test_04_semantic_similarity_evaluation(self):
        """Test evaluation with semantically similar answers."""
        print("\n--- Testing Semantic Similarity Evaluation ---")
        
        data = self.test_data['semantic_similar']
        result = self.evaluator.evaluate(data['student'], data['reference'])
        
        # Semantically similar should have high score
        self.assertGreater(result['details']['raw_score'], 0.7)
        self.assertGreater(result['final_score'], 0)
        self.assertFalse(result['details']['filtered'])
        
        print(f"✓ Semantic similarity: Raw score = {result['details']['raw_score']:.4f}, "
              f"Final score = {result['final_score']:.2f}")
    
    def test_05_partial_match_evaluation(self):
        """Test evaluation with partial matches."""
        print("\n--- Testing Partial Match Evaluation ---")
        
        data = self.test_data['partial_match']
        result = self.evaluator.evaluate(data['student'], data['reference'])
        
        # Partial match should have moderate score
        self.assertGreater(result['details']['raw_score'], 0.3)
        self.assertLess(result['details']['raw_score'], 0.8)
        
        print(f"✓ Partial match: Raw score = {result['details']['raw_score']:.4f}, "
              f"Final score = {result['final_score']:.2f}")
    
    def test_06_irrelevant_answer_evaluation(self):
        """Test evaluation with irrelevant answers."""
        print("\n--- Testing Irrelevant Answer Evaluation ---")
        
        data = self.test_data['different_topic']
        result = self.evaluator.evaluate(data['student'], data['reference'])
        
        # Irrelevant answer should have low score and be filtered
        self.assertLess(result['details']['raw_score'], self.evaluator.threshold)
        self.assertEqual(result['final_score'], 0.0)
        self.assertTrue(result['details']['filtered'])
        self.assertEqual(result['details']['category'], 'Filtered (Irrelevant)')
        
        print(f"✓ Irrelevant answer: Raw score = {result['details']['raw_score']:.4f}, "
              f"Filtered = {result['details']['filtered']}")
    
    def test_07_empty_answer_evaluation(self):
        """Test evaluation with empty answers."""
        print("\n--- Testing Empty Answer Evaluation ---")
        
        data = self.test_data['empty_answer']
        result = self.evaluator.evaluate(data['student'], data['reference'])
        
        # Empty answer should return 0 score
        self.assertEqual(result['final_score'], 0.0)
        self.assertEqual(result['details']['raw_score'], 0.0)
        self.assertTrue(result['details']['filtered'])
        self.assertEqual(result['details']['reason'], 'Empty answer')
        
        print("✓ Empty answer handled correctly")
    
    def test_08_whitespace_only_evaluation(self):
        """Test evaluation with whitespace-only answers."""
        print("\n--- Testing Whitespace-Only Answer Evaluation ---")
        
        data = self.test_data['whitespace_only']
        result = self.evaluator.evaluate(data['student'], data['reference'])
        
        # Whitespace-only should be treated as empty
        self.assertEqual(result['final_score'], 0.0)
        self.assertTrue(result['details']['filtered'])
        
        print("✓ Whitespace-only answer handled correctly")
    
    def test_09_complex_question_evaluation(self):
        """Test evaluation with complex scientific questions."""
        print("\n--- Testing Complex Question Evaluation ---")
        
        data = self.test_data['complex_question']
        result = self.evaluator.evaluate(data['student'], data['reference'])
        
        # Complex scientific answer should have good semantic understanding
        self.assertGreater(result['details']['raw_score'], 0.6)
        self.assertGreater(result['final_score'], 0)
        self.assertFalse(result['details']['filtered'])
        
        print(f"✓ Complex question: Raw score = {result['details']['raw_score']:.4f}, "
              f"Final score = {result['final_score']:.2f}")
    
    def test_10_batch_evaluation(self):
        """Test batch evaluation functionality."""
        print("\n--- Testing Batch Evaluation ---")
        
        # Prepare batch data
        student_answers = [
            self.test_data['exact_match']['student'],
            self.test_data['semantic_similar']['student'],
            self.test_data['different_topic']['student'],
            self.test_data['empty_answer']['student']
        ]
        reference_answers = [
            self.test_data['exact_match']['reference'],
            self.test_data['semantic_similar']['reference'],
            self.test_data['different_topic']['reference'],
            self.test_data['empty_answer']['reference']
        ]
        
        batch_result = self.evaluator.evaluate_batch(student_answers, reference_answers)
        
        # Verify batch result structure
        self.assertIn('results', batch_result)
        self.assertIn('summary', batch_result)
        self.assertEqual(len(batch_result['results']), 4)
        self.assertEqual(batch_result['summary']['total_questions'], 4)
        
        # Check individual results
        self.assertGreater(batch_result['results'][0]['final_score'], 0)  # Exact match
        self.assertGreater(batch_result['results'][1]['final_score'], 0)  # Semantic similar
        self.assertEqual(batch_result['results'][2]['final_score'], 0)    # Different topic
        self.assertEqual(batch_result['results'][3]['final_score'], 0)    # Empty answer
        
        print(f"✓ Batch evaluation: {batch_result['summary']['total_questions']} questions, "
              f"{batch_result['summary']['filtered_answers']} filtered, "
              f"avg score = {batch_result['summary']['average_score']:.2f}")
    
    def test_11_different_thresholds(self):
        """Test evaluation with different threshold values."""
        print("\n--- Testing Different Thresholds ---")
        
        test_answer = "Paris is the capital of France."
        reference_answer = "The capital of France is Paris."
        
        # Test with low threshold (0.3)
        self.evaluator.set_threshold(0.3)
        result_low = self.evaluator.evaluate(test_answer, reference_answer)
        
        # Test with high threshold (0.8)
        self.evaluator.set_threshold(0.8)
        result_high = self.evaluator.evaluate(test_answer, reference_answer)
        
        # Both should have same raw score but different final scores based on threshold
        self.assertEqual(result_low['details']['raw_score'], result_high['details']['raw_score'])
        
        # Reset to original threshold
        self.evaluator.set_threshold(0.6)
        
        print(f"✓ Different thresholds: Raw score = {result_low['details']['raw_score']:.4f}, "
              f"Low threshold result = {result_low['final_score']:.2f}, "
              f"High threshold result = {result_high['final_score']:.2f}")
    
    def test_12_model_info(self):
        """Test model information retrieval."""
        print("\n--- Testing Model Information ---")
        
        model_info = self.evaluator.get_model_info()
        
        # Verify model info structure
        self.assertIn('model_name', model_info)
        self.assertIn('device', model_info)
        self.assertIn('threshold', model_info)
        self.assertIn('max_marks', model_info)
        
        # Verify values
        self.assertEqual(model_info['model_name'], 'cross-encoder/stsb-roberta-large')
        self.assertEqual(model_info['device'], 'cpu')
        self.assertEqual(model_info['threshold'], self.evaluator.threshold)
        self.assertEqual(model_info['max_marks'], self.evaluator.max_marks)
        
        print("✓ Model information retrieved correctly")
    
    def test_13_quality_categories(self):
        """Test quality category assignment."""
        print("\n--- Testing Quality Categories ---")
        
        # Test different score ranges
        test_cases = [
            (0.9, False, "Excellent"),
            (0.7, False, "Good"),
            (0.5, False, "Fair"),
            (0.3, False, "Poor"),
            (0.2, True, "Filtered (Irrelevant)")
        ]
        
        for raw_score, filtered, expected_category in test_cases:
            category = self.evaluator._get_quality_category(raw_score, filtered)
            self.assertEqual(category, expected_category)
        
        print("✓ Quality categories assigned correctly")
    
    def test_14_error_handling(self):
        """Test error handling in batch evaluation."""
        print("\n--- Testing Error Handling ---")
        
        # Test mismatched list lengths
        with self.assertRaises(ValueError):
            self.evaluator.evaluate_batch(["answer1"], ["ref1", "ref2"])
        
        print("✓ Error handling works correctly")
    
    def test_15_performance_benchmark(self):
        """Test performance with multiple evaluations."""
        print("\n--- Testing Performance Benchmark ---")
        
        import time
        
        # Prepare test data
        test_pairs = [
            ("The capital of France is Paris.", "Paris is the capital of France."),
            ("Water boils at 100 degrees Celsius.", "The boiling point of water is 100°C."),
            ("Photosynthesis produces oxygen.", "Plants release oxygen during photosynthesis."),
            ("Gravity pulls objects downward.", "Objects fall due to gravitational force."),
            ("The sun is a star.", "Our sun is classified as a star.")
        ]
        
        # Time the evaluations
        start_time = time.time()
        
        for student, reference in test_pairs:
            result = self.evaluator.evaluate(student, reference)
            self.assertIsNotNone(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✓ Performance test: {len(test_pairs)} evaluations in {total_time:.2f} seconds "
              f"({total_time/len(test_pairs):.3f} seconds per evaluation)")
    
    def setUp(self):
        """Set up each test with evaluator instance."""
        if not hasattr(self, 'evaluator'):
            self.evaluator = OptimizedSASEvaluator(device="cpu", threshold=0.6, max_marks=10)
        
        if not hasattr(self, 'test_data'):
            self.test_data = {
                'exact_match': {
                    'student': "The capital of France is Paris.",
                    'reference': "The capital of France is Paris.",
                    'expected_category': 'Excellent'
                },
                'semantic_similar': {
                    'student': "Paris serves as the capital city of France.",
                    'reference': "The capital of France is Paris.",
                    'expected_category': 'Excellent'
                },
                'partial_match': {
                    'student': "France has a capital city.",
                    'reference': "The capital of France is Paris.",
                    'expected_category': 'Good'
                },
                'different_topic': {
                    'student': "The weather is sunny today.",
                    'reference': "The capital of France is Paris.",
                    'expected_category': 'Filtered (Irrelevant)'
                },
                'empty_answer': {
                    'student': "",
                    'reference': "The capital of France is Paris.",
                    'expected_category': 'Filtered'
                },
                'whitespace_only': {
                    'student': "   \n\t  ",
                    'reference': "The capital of France is Paris.",
                    'expected_category': 'Filtered'
                },
                'complex_question': {
                    'student': "Photosynthesis is the process where plants use sunlight, water, and carbon dioxide to produce glucose and oxygen.",
                    'reference': "Photosynthesis is a process in which plants convert light energy into chemical energy, producing glucose and releasing oxygen.",
                    'expected_category': 'Excellent'
                }
            }

    def run_comprehensive_test(self):
        """Run all tests and provide summary."""
        print("\n" + "="*60)
        print("RUNNING COMPREHENSIVE TEST SUITE")
        print("="*60)
        
        # Set up the test instance
        self.setUp()
        
        test_methods = [
            self.test_01_initialization,
            self.test_02_threshold_update,
            self.test_03_exact_match_evaluation,
            self.test_04_semantic_similarity_evaluation,
            self.test_05_partial_match_evaluation,
            self.test_06_irrelevant_answer_evaluation,
            self.test_07_empty_answer_evaluation,
            self.test_08_whitespace_only_evaluation,
            self.test_09_complex_question_evaluation,
            self.test_10_batch_evaluation,
            self.test_11_different_thresholds,
            self.test_12_model_info,
            self.test_13_quality_categories,
            self.test_14_error_handling,
            self.test_15_performance_benchmark
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            try:
                test_method()
                passed_tests += 1
            except Exception as e:
                print(f"✗ {test_method.__name__} failed: {str(e)}")
        
        print("\n" + "="*60)
        print("TEST SUITE SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! OptimizedSASEvaluator is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the errors above.")
        
        return passed_tests == total_tests

def main():
    """Main function to run the test suite."""
    print("OptimizedSASEvaluator Test Suite")
    print("This test suite will validate all functionality of the OptimizedSASEvaluator class.")
    
    # Create test instance
    test_suite = TestOptimizedSASEvaluator()
    
    # Run comprehensive test
    success = test_suite.run_comprehensive_test()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
