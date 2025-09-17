#!/usr/bin/env python3
"""
LLM-based Answer Evaluator using Ollama and Llama 7B
====================================================

This module provides an LLM-based evaluation system that uses Ollama with Llama 7B
to evaluate student answers. The evaluator provides detailed scoring with explanations
that can be reviewed and approved by administrators.
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Try to import PrimaryFilter, but make it optional
try:
    from optimized_sas_evaluator import PrimaryFilter
    PRIMARY_FILTER_AVAILABLE = True
except ImportError:
    PrimaryFilter = None
    PRIMARY_FILTER_AVAILABLE = False

logger = logging.getLogger(__name__)

class LLMEvaluator:
    """LLM-based evaluator using Ollama and Llama 7B model."""
    
    def __init__(self, 
                 ollama_url: str = "http://localhost:11434",
                 model_name: str = "llama2:latest",
                 max_retries: int = 3,
                 timeout: int = 60,
                 sas_threshold: float = 0.15):
        """
        Initialize the LLM evaluator with SAS quality filter.
        
        Args:
            ollama_url: URL of the Ollama server
            model_name: Name of the model to use (default: llama2:latest)
            max_retries: Maximum number of retries for API calls
            timeout: Timeout for API calls in seconds
            sas_threshold: SAS similarity threshold for quality filtering
        """
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.max_retries = max_retries
        self.timeout = timeout
        self.filter_threshold = 0.3  # Balanced threshold for filtering
        self.is_available = False
        
        # Initialize primary filter for quality filtering (if available)
        if PRIMARY_FILTER_AVAILABLE:
            try:
                self.primary_filter = PrimaryFilter(threshold=0.3)
                print(f"✅ Primary Filter initialized with threshold: 0.3")
            except Exception as e:
                print(f"❌ Failed to initialize primary filter: {e}")
                print("⚠️ Continuing without primary filter - LLM evaluation only")
                self.primary_filter = None
        else:
            print("⚠️ Primary Filter not available - LLM evaluation only")
            self.primary_filter = None
        
        # Test connection and model availability
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to Ollama and model availability."""
        try:
            # Test if Ollama is running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.model_name in model_names:
                    self.is_available = True
                    logger.info(f"✅ LLM Evaluator initialized successfully with model: {self.model_name}")
                else:
                    logger.warning(f"⚠️ Model {self.model_name} not found. Available models: {model_names}")
                    # Try to use the first available model
                    if model_names:
                        self.model_name = model_names[0]
                        self.is_available = True
                        logger.info(f"🔄 Using available model: {self.model_name}")
                    else:
                        logger.error("❌ No models available in Ollama")
            else:
                logger.error(f"❌ Failed to connect to Ollama: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error connecting to Ollama: {str(e)}")
            logger.info("💡 Make sure Ollama is running: ollama serve")
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Make a call to the Ollama API.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            Response from the model or None if failed
        """
        if not self.is_available:
            logger.error("LLM Evaluator is not available")
            return None
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower temperature for more consistent evaluation
                "top_p": 0.9,
                "max_tokens": 1000
            }
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', '').strip()
                else:
                    logger.warning(f"Attempt {attempt + 1}: HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}: {str(e)}")
                
            if attempt < self.max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error("Failed to get response from Ollama after all retries")
        return None
    
    def _create_evaluation_prompt(self, 
                                 question: str, 
                                 reference_answer: str, 
                                 student_answer: str,
                                 max_marks: int,
                                 similarity_score: float = 0.0) -> str:
        """
        Create a comprehensive educational evaluation prompt for the LLM.
        
        Args:
            question: The exam question
            reference_answer: The reference/expected answer
            student_answer: The student's answer
            max_marks: Maximum marks for this question
            similarity_score: Similarity score from primary filter (0.0-1.0)
            
        Returns:
            Formatted prompt for the LLM
        """
        prompt = f"""You are an expert educational evaluator. Evaluate the student's answer based on conceptual understanding and provide a percentage score.

CRITICAL: If the student's answer is completely unrelated to the question topic or shows no understanding, give 0% immediately.

Student Answer: {student_answer}
Reference Answer: {reference_answer}

EVALUATION CRITERIA:
1. Conceptual Accuracy (40%): Core concepts correctly identified and explained
2. Completeness (30%): Addresses key points from reference answer
3. Depth & Coverage (15%): Sufficient detail and comprehensive coverage
4. Clarity & Communication (15%): Clear, well-organized explanation

SCORING GUIDELINES:
- 90-100%: Excellent understanding, comprehensive coverage
- 80-89%: Strong understanding, addresses most key points
- 70-79%: Good understanding, covers main concepts
- 60-69%: Adequate understanding, partial coverage
- 50-59%: Basic understanding, significant gaps
- 40-49%: Limited understanding, major gaps
- 30-39%: Poor understanding, minimal knowledge
- 20-29%: Very poor understanding, mostly incorrect
- 10-19%: Minimal understanding, mostly wrong
- 0-9%: No understanding, completely incorrect or unrelated

EVALUATION RULES:
- Focus on CONCEPTUAL UNDERSTANDING, not exact wording
- Accept equivalent concepts expressed differently
- Reward comprehensive coverage even if details differ
- Give 0% for answers showing no understanding of the topic
- Give 0% for completely unrelated or nonsensical answers
- Give 0% for answers that are clearly wrong or demonstrate no knowledge
- Be fair but strict - partial credit only for actual understanding
- Ignore the similarity score - evaluate independently
- If answer is unrelated to the question topic, give 0% immediately

REQUIRED FORMAT:
Score: [percentage from 0% to 100%]
Reason: [Brief explanation of the student's understanding level and what they got right or wrong]

Now evaluate:"""

        return prompt
    
    def evaluate(self, 
                 student_answer: str, 
                 reference_answer: str,
                 question: str = "",
                 max_marks: int = 10) -> Dict[str, Any]:
        """
        Evaluate a student's answer using the LLM.
        
        Args:
            student_answer: The student's answer
            reference_answer: The reference answer
            question: The exam question (optional)
            max_marks: Maximum marks for this question
            
        Returns:
            Dictionary containing evaluation results
        """
        if not self.is_available:
            return {
                'score': 0.0,
                'explanation': 'System error: LLM not available',
                'details': {
                    'error': 'LLM Evaluator not available',
                    'llm_score': 0.0,
                    'status': 'error',
                    'model_name': self.model_name,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        
        if not student_answer or not student_answer.strip():
            return {
                'score': 0.0,
                'explanation': 'No answer provided',
                'details': {
                    'llm_score': 0.0,
                    'status': 'empty_answer',
                    'model_name': self.model_name,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        
        try:
            # Step 1: Primary Quality Filter - Check if answer is relevant enough for LLM evaluation
            filter_passed = True
            filter_score = 0.0
            filter_reason = ""
            
            if self.primary_filter:
                try:
                    filter_result = self.primary_filter.evaluate(student_answer, reference_answer)
                    filter_score = filter_result['details']['raw_score']
                    filter_passed = not filter_result['details']['filtered']
                    filter_reason = filter_result['details']['reason']
                    
                    print(f"🔍 Primary Filter: Score={filter_score:.3f}, Passed={filter_passed}, Reason={filter_reason}")
                    
                    # If filter score is too low, skip LLM evaluation
                    if not filter_passed or filter_score < self.filter_threshold:
                        return {
                            'final_score': 0.0,
                            'explanation': 'Irrelevant answer',
                            'details': {
                                'llm_score': 0.0,
                                'status': 'filtered',
                                'model_name': self.model_name,
                                'filter_score': filter_score,
                                'filter_threshold': self.filter_threshold,
                                'filter_passed': False,
                                'timestamp': datetime.utcnow().isoformat()
                            }
                        }
                except Exception as e:
                    print(f"⚠️ Primary filter evaluation failed: {e}, proceeding with LLM evaluation")
            
            # Step 2: LLM Evaluation (only if primary filter passes)
            prompt = self._create_evaluation_prompt(
                question=question,
                reference_answer=reference_answer,
                student_answer=student_answer,
                max_marks=max_marks,
                similarity_score=filter_score
            )
            
            # Get LLM response
            llm_response = self._call_ollama(prompt)
            
            if not llm_response:
                return {
                    'final_score': 0.0,
                    'explanation': 'System error: Could not evaluate answer',
                    'details': {
                        'error': 'Failed to get LLM response',
                        'llm_score': 0.0,
                        'status': 'error',
                        'model_name': self.model_name,
                        'filter_score': filter_score,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
            
            # Parse LLM response
            llm_score, llm_explanation = self._parse_llm_response(llm_response, max_marks)
            
            # Step 3: Apply External Length Penalty
            length_ratio = (len(student_answer) / len(reference_answer)) * 100
            score = self._apply_length_penalty(llm_score, length_ratio, max_marks)
            
            # Update explanation if length penalty was applied
            if score < llm_score:
                explanation = f"{llm_explanation} (Length penalty applied: {length_ratio:.1f}% of reference length)"
            else:
                explanation = llm_explanation
            
            # Step 4: Validate score range
            if score < 0 or score > max_marks:
                print(f"⚠️ Final score out of range: {score}, clamping to valid range")
                score = max(0, min(score, max_marks))
                explanation = f"Score adjusted to valid range. {explanation}"
            
            # Step 4: Score validation (no consistency check)
            
            return {
                'final_score': score,
                'explanation': explanation,
                'details': {
                    'llm_score': score,
                    'status': 'evaluated',
                    'model_name': self.model_name,
                    'raw_response': llm_response,
                    'filter_score': filter_score,
                    'filter_threshold': self.filter_threshold,
                    'filter_passed': filter_passed,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in LLM evaluation: {str(e)}")
            return {
                'final_score': 0.0,
                'explanation': 'System error during evaluation',
                'details': {
                    'error': str(e),
                    'llm_score': 0.0,
                    'status': 'error',
                    'model_name': self.model_name,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
    
    def _parse_llm_response(self, response: str, max_marks: int) -> tuple[float, str]:
        """
        Parse the LLM response to extract score and explanation.
        
        Args:
            response: Raw response from LLM
            max_marks: Maximum possible marks
            
        Returns:
            Tuple of (score, explanation)
        """
        try:
            lines = response.strip().split('\n')
            score = 0.0
            explanation = "No explanation provided"
            
            for line in lines:
                line = line.strip()
                if line.startswith('Score:'):
                    # Extract score
                    score_text = line.replace('Score:', '').strip()
                    try:
                        # Handle percentage scores (e.g., "85%", "85")
                        if '%' in score_text:
                            score_text = score_text.replace('%', '').strip()
                            percentage = float(score_text)
                            # Convert percentage to max_marks scale
                            score = (percentage / 100.0) * max_marks
                        else:
                            # Handle direct scores
                            score = float(score_text)
                            # If score is > 100, assume it's a percentage
                            if score > 100:
                                score = (score / 100.0) * max_marks
                        
                        # Ensure score is within valid range
                        score = max(0, min(score, max_marks))
                    except ValueError:
                        logger.warning(f"Could not parse score: {score_text}")
                        score = 0.0
                        
                elif 'Score:' in line and not line.startswith('Score:'):
                    # Handle case where Score: appears in the middle of a line
                    score_text = line.split('Score:')[-1].strip()
                    try:
                        # Handle percentage scores (e.g., "85%", "85")
                        if '%' in score_text:
                            score_text = score_text.replace('%', '').strip()
                            percentage = float(score_text)
                            # Convert percentage to max_marks scale
                            score = (percentage / 100.0) * max_marks
                        else:
                            # Handle direct scores
                            score = float(score_text)
                            # If score is > 100, assume it's a percentage
                            if score > 100:
                                score = (score / 100.0) * max_marks
                        
                        # Ensure score is within valid range
                        score = max(0, min(score, max_marks))
                    except ValueError:
                        logger.warning(f"Could not parse score: {score_text}")
                        score = 0.0
                        
                elif 'percentage score of' in line.lower():
                    # Handle case where LLM says "I would give a percentage score of X%"
                    try:
                        # Extract percentage from line
                        import re
                        match = re.search(r'(\d+(?:\.\d+)?)%', line)
                        if match:
                            percentage = float(match.group(1))
                            score = (percentage / 100.0) * max_marks
                            score = max(0, min(score, max_marks))
                    except (ValueError, AttributeError):
                        logger.warning(f"Could not parse percentage from line: {line}")
                        score = 0.0
                        
                elif line.startswith('Reason:'):
                    # Extract reason - single line explanation
                    explanation = line.replace('Reason:', '').strip()
            
            return score, explanation
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return 0.0, "Error parsing evaluation response"
    
    def _apply_length_penalty(self, llm_score: float, length_ratio: float, max_marks: int) -> float:
        """
        Apply external length penalty to LLM score based on length ratio.
        
        Args:
            llm_score: Score from LLM (0 to max_marks)
            length_ratio: Length ratio as percentage (0-100+)
            max_marks: Maximum marks for the question
            
        Returns:
            Final score after applying length penalty
        """
        # Convert LLM score to percentage for easier calculation
        llm_percentage = (llm_score / max_marks) * 100
        
        # Apply length penalty rules (more lenient thresholds)
        if length_ratio < 5:
            # Less than 5% of reference length: MAXIMUM 30%
            max_allowed_percentage = 30
        elif length_ratio < 15:
            # Less than 15% of reference length: MAXIMUM 50%
            max_allowed_percentage = 50
        elif length_ratio < 25:
            # Less than 25% of reference length: MAXIMUM 70%
            max_allowed_percentage = 70
        else:
            # 25% or more: No length penalty
            max_allowed_percentage = 100
        
        # Apply the penalty
        final_percentage = min(llm_percentage, max_allowed_percentage)
        
        # Convert back to max_marks scale
        final_score = (final_percentage / 100) * max_marks
        
        return final_score
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model and system status."""
        return {
            'model_name': self.model_name,
            'ollama_url': self.ollama_url,
            'is_available': self.is_available,
            'max_retries': self.max_retries,
            'timeout': self.timeout
        }
    
    def test_evaluation(self) -> Dict[str, Any]:
        """
        Test the evaluation system with a sample question.
        
        Returns:
            Test results
        """
        test_question = "What is photosynthesis?"
        test_reference = "Photosynthesis is the process by which plants convert light energy into chemical energy, using carbon dioxide and water to produce glucose and oxygen."
        test_student_answer = "Photosynthesis is how plants make food using sunlight, water, and carbon dioxide."
        
        return self.evaluate(
            student_answer=test_student_answer,
            reference_answer=test_reference,
            question=test_question,
            max_marks=10
        )


# Example usage and testing
if __name__ == "__main__":
    # Initialize evaluator
    evaluator = LLMEvaluator()
    
    # Test connection
    print("Model Info:", evaluator.get_model_info())
    
    # Test evaluation
    if evaluator.is_available:
        print("\nTesting evaluation...")
        result = evaluator.test_evaluation()
        print("Test Result:", json.dumps(result, indent=2))
    else:
        print("LLM Evaluator is not available. Make sure Ollama is running with llama2:7b model.")
