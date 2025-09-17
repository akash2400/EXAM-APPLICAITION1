#!/usr/bin/env python3
"""
Primary Filter System for Answer Quality Assessment
Integrated with the exam application - allows admin threshold configuration.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
import sys
import os
from typing import List, Tuple, Dict, Any

class PrimaryFilter:
    """Primary filter for answer quality assessment integrated with exam system."""
    
    def __init__(self, device: str = "cpu", threshold: float = 0.6, max_marks: int = 10):
        """
        Initialize the primary filter system.
        
        Args:
            device: Device to run the model on ("cpu" or "cuda")
            threshold: Minimum similarity threshold (scores below this become 0)
            max_marks: Maximum marks for scaling (default 10 for compatibility)
        """
        self.device = device
        self.model = None
        self.model_name = "all-mpnet-base-v2"
        self.batch_size = 8
        self.threshold = threshold
        self.max_marks = max_marks
        
        print(f"Initializing Primary Filter System - Threshold: {self.threshold}, Max marks: {self.max_marks}")
        self._load_model()
    
    def _load_model(self):
        """Load and configure the optimal model."""
        try:
            # Load model using SentenceTransformer
            print(f"Loading model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            
            print("Model loaded and configured successfully")
            print("PrimaryFilter initialized successfully")
            
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            raise e
    
    def set_threshold(self, threshold: float):
        """Update the similarity threshold."""
        self.threshold = threshold
        print(f"Threshold updated to: {self.threshold}")
    
    def evaluate(self, student_answer: str, reference_answer: str) -> Dict[str, Any]:
        """
        Evaluate a single answer pair - compatible with existing application interface.
        
        Args:
            student_answer: Student's answer
            reference_answer: Reference answer
            
        Returns:
            Dictionary containing final_score and details for compatibility
        """
        if not student_answer or not student_answer.strip():
            return {
                'final_score': 0.0,
                'details': {
                    'raw_score': 0.0,
                    'filtered': True,
                    'reason': 'Empty answer',
                    'threshold': self.threshold,
                    'category': 'Filtered',
                    'model_name': self.model_name
                }
            }
        
        # Get raw similarity score from the model
        raw_score = self._compute_similarity(reference_answer, student_answer)
        
        # Apply threshold filtering - let the model's semantic understanding do the work
        if raw_score < self.threshold:
            final_score = 0.0
            filtered = True
            reason = f"Score {raw_score:.4f} below threshold {self.threshold}"
        else:
            # Scale to max_marks (raw scores are typically 0-1, scale to 0-max_marks)
            final_score = raw_score * self.max_marks
            filtered = False
            reason = "Passed threshold"
        
        # Determine quality category
        category = self._get_quality_category(raw_score, filtered)
        
        return {
            'final_score': final_score,
            'details': {
                'raw_score': raw_score,
                'filtered': filtered,
                'reason': reason,
                'threshold': self.threshold,
                'category': category,
                'model_name': self.model_name
            }
        }
    
    def evaluate_batch(self, student_answers: List[str], reference_answers: List[str]) -> Dict[str, Any]:
        """
        Evaluate multiple answer pairs for detailed analysis.
        
        Args:
            student_answers: List of student answers
            reference_answers: List of reference answers
            
        Returns:
            Dictionary containing detailed results
        """
        if len(student_answers) != len(reference_answers):
            raise ValueError("Number of student answers must match reference answers")
        
        results = []
        total_score = 0.0
        filtered_count = 0
        
        for i, (student_answer, reference_answer) in enumerate(zip(student_answers, reference_answers)):
            result = self.evaluate(student_answer, reference_answer)
            results.append(result)
            total_score += result['final_score']
            if result['details']['filtered']:
                filtered_count += 1
        
        avg_score = total_score / len(results) if results else 0.0
        
        return {
            'results': results,
            'summary': {
                'total_questions': len(results),
                'filtered_answers': filtered_count,
                'average_score': avg_score,
                'total_score': total_score,
                'threshold': self.threshold
            }
        }
    
    def _get_quality_category(self, raw_score: float, filtered: bool) -> str:
        """Determine quality category based on raw score."""
        if filtered:
            return "Filtered (Irrelevant)"
        elif raw_score >= 0.8:
            return "Excellent"
        elif raw_score >= 0.6:
            return "Good"
        elif raw_score >= 0.4:
            return "Fair"
        else:
            return "Poor"
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity between two texts using the model."""
        try:
            # Get embeddings using SentenceTransformer
            embeddings = self.model.encode([text1, text2])
            
            # Compute cosine similarity
            similarity = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
            
            return float(similarity)
                
        except Exception as e:
            print(f"Error computing similarity: {e}")
            return 0.0
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'batch_size': self.batch_size,
            'threshold': self.threshold,
            'max_marks': self.max_marks
        }