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

logger = logging.getLogger(__name__)

class LLMEvaluator:
    """LLM-based evaluator using Ollama and Llama 7B model."""
    
    def __init__(self, 
                 ollama_url: str = "http://localhost:11434",
                 model_name: str = "llama2:latest",
                 max_retries: int = 3,
                 timeout: int = 60):
        """
        Initialize the LLM evaluator.
        
        Args:
            ollama_url: URL of the Ollama server
            model_name: Name of the model to use (default: llama2:7b)
            max_retries: Maximum number of retries for API calls
            timeout: Timeout for API calls in seconds
        """
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.max_retries = max_retries
        self.timeout = timeout
        self.is_available = False
        
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
                                 max_marks: int) -> str:
        """
        Create a comprehensive evaluation prompt for the LLM.
        
        Args:
            question: The exam question
            reference_answer: The reference/expected answer
            student_answer: The student's answer
            max_marks: Maximum marks for this question
            
        Returns:
            Formatted prompt for the LLM
        """
        prompt = f"""You are an expert academic evaluator. Your task is to evaluate a student's answer against a reference answer and provide a detailed assessment.

EVALUATION CRITERIA:
1. Content Accuracy: How well does the student's answer address the question?
2. Knowledge Depth: Does the answer demonstrate understanding of key concepts?
3. Completeness: Is the answer comprehensive and complete?
4. Clarity: Is the answer well-structured and clear?
5. Relevance: Does the answer stay on topic and address the question directly?

QUESTION:
{question}

REFERENCE ANSWER:
{reference_answer}

STUDENT ANSWER:
{student_answer}

MAXIMUM MARKS: {max_marks}

EVALUATION INSTRUCTIONS:
- Provide a score from 0 to {max_marks} (where {max_marks} is perfect)
- Give a brief one-line explanation for your scoring decision
- Consider partial credit for partially correct answers
- Be fair but rigorous in your assessment
- Focus on the student's understanding rather than exact wording

RESPONSE FORMAT (EXACTLY):
Score: [number from 0 to {max_marks}]
Explanation: [one-line explanation of the scoring decision]

Example:
Score: 7
Explanation: Good understanding of main concepts with minor gaps in explanation.

Now evaluate the student's answer:"""

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
                'final_score': 0.0,
                'details': {
                    'error': 'LLM Evaluator not available',
                    'llm_score': 0.0,
                    'explanation': 'System error: LLM not available',
                    'status': 'error',
                    'model_name': self.model_name,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        
        if not student_answer or not student_answer.strip():
            return {
                'final_score': 0.0,
                'details': {
                    'llm_score': 0.0,
                    'explanation': 'No answer provided',
                    'status': 'empty_answer',
                    'model_name': self.model_name,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        
        try:
            # Create evaluation prompt
            prompt = self._create_evaluation_prompt(
                question=question,
                reference_answer=reference_answer,
                student_answer=student_answer,
                max_marks=max_marks
            )
            
            # Get LLM response
            llm_response = self._call_ollama(prompt)
            
            if not llm_response:
                return {
                    'final_score': 0.0,
                    'details': {
                        'error': 'Failed to get LLM response',
                        'llm_score': 0.0,
                        'explanation': 'System error: Could not evaluate answer',
                        'status': 'error',
                        'model_name': self.model_name,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
            
            # Parse LLM response
            score, explanation = self._parse_llm_response(llm_response, max_marks)
            
            return {
                'final_score': score,
                'details': {
                    'llm_score': score,
                    'explanation': explanation,
                    'status': 'evaluated',
                    'model_name': self.model_name,
                    'raw_response': llm_response,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in LLM evaluation: {str(e)}")
            return {
                'final_score': 0.0,
                'details': {
                    'error': str(e),
                    'llm_score': 0.0,
                    'explanation': 'System error during evaluation',
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
                        score = float(score_text)
                        # Ensure score is within valid range
                        score = max(0, min(score, max_marks))
                    except ValueError:
                        logger.warning(f"Could not parse score: {score_text}")
                        score = 0.0
                        
                elif line.startswith('Explanation:'):
                    # Extract explanation
                    explanation = line.replace('Explanation:', '').strip()
            
            return score, explanation
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return 0.0, "Error parsing evaluation response"
    
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
