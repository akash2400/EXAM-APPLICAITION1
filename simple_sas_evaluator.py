#!/usr/bin/env python3
"""
Simple SAS Evaluator using basic text similarity
"""

import re
from typing import Dict, Any
from difflib import SequenceMatcher

class SimpleSASEvaluator:
    """Simple SAS evaluator using basic text similarity metrics."""
    
    def __init__(self, threshold: float = 0.15, max_marks: int = 10):
        self.threshold = threshold
        self.max_marks = max_marks
        self.model_name = "simple-text-similarity"
        
        print(f"Initializing Simple SAS System - Threshold: {self.threshold}, Max marks: {self.max_marks}")
        print("SimpleSASEvaluator initialized successfully")
    
    def evaluate(self, student_answer: str, reference_answer: str) -> Dict[str, Any]:
        """
        Evaluate similarity between student and reference answers.
        
        Args:
            student_answer: Student's answer
            reference_answer: Reference answer
            
        Returns:
            Dictionary with evaluation results
        """
        # Clean and normalize text
        student_clean = self._clean_text(student_answer)
        reference_clean = self._clean_text(reference_answer)
        
        # Check for very short or nonsensical answers
        if len(student_clean) < 3:
            return {
                'score': 0.0,
                'raw_score': 0.0,
                'filtered': True,
                'quality': 'Poor',
                'details': {
                    'reason': 'Answer too short',
                    'category': 'Filtered',
                    'model_name': self.model_name
                }
            }
        
        # Compute similarity using multiple methods
        similarity_score = self._compute_similarity(student_clean, reference_clean)
        
        # Apply threshold filtering
        if similarity_score < self.threshold:
            final_score = 0.0
            filtered = True
        else:
            final_score = similarity_score * self.max_marks
            filtered = False
        
        # Determine quality
        quality = self._get_quality_label(similarity_score)
        
        return {
            'score': final_score,
            'raw_score': similarity_score,
            'filtered': filtered,
            'quality': quality,
            'details': {
                'reason': 'SAS evaluation completed',
                'category': 'Evaluated',
                'model_name': self.model_name,
                'similarity_methods': 'sequence_matcher + word_overlap'
            }
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for comparison."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation for better matching
        text = re.sub(r'[^\w\s]', '', text)
        
        return text
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity using multiple methods."""
        if not text1 or not text2:
            return 0.0
        
        # Method 1: Sequence matcher
        seq_similarity = SequenceMatcher(None, text1, text2).ratio()
        
        # Method 2: Word overlap
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            word_similarity = 0.0
        else:
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            word_similarity = len(intersection) / len(union) if union else 0.0
        
        # Method 3: Length similarity (penalize very different lengths)
        len1, len2 = len(text1), len(text2)
        length_similarity = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 0.0
        
        # Combine methods with weights
        combined_score = (
            seq_similarity * 0.5 +      # 50% sequence similarity
            word_similarity * 0.3 +     # 30% word overlap
            length_similarity * 0.2     # 20% length similarity
        )
        
        return min(1.0, max(0.0, combined_score))
    
    def _get_quality_label(self, raw_score: float) -> str:
        """Get quality label based on raw score."""
        if raw_score >= 0.8:
            return "Excellent"
        elif raw_score >= 0.6:
            return "Good"
        elif raw_score >= 0.4:
            return "Fair"
        else:
            return "Poor"
    
    def set_threshold(self, threshold: float):
        """Update the similarity threshold."""
        self.threshold = threshold
        print(f"Threshold updated to: {self.threshold}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the evaluator."""
        return {
            'model_name': self.model_name,
            'threshold': self.threshold,
            'max_marks': self.max_marks,
            'type': 'simple_text_similarity'
        }
