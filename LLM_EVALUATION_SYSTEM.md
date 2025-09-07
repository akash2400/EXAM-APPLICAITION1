# LLM Evaluation System Documentation

## Overview

The exam application has been upgraded to use an LLM-based evaluation system powered by Ollama and Llama 7B model. This system provides intelligent answer evaluation with detailed explanations that require administrator approval before final scores are released to students.

## Architecture Changes

### Previous System (SAS Evaluator)
- Automatic scoring using Semantic Answer Similarity
- Immediate score release to students
- No human oversight required

### New System (LLM Evaluator)
- LLM-powered evaluation using Ollama + Llama 7B
- Detailed explanations for each score
- Administrator review and approval workflow
- Pending status for students until approval

## Key Components

### 1. LLM Evaluator (`llm_evaluator.py`)
- **Purpose**: Evaluates student answers using Ollama API
- **Model**: Llama 7B (configurable)
- **Features**:
  - Comprehensive evaluation prompts
  - Score and explanation generation
  - Error handling and retry logic
  - Connection testing

### 2. Database Schema Updates
New fields added to `Result` table:
- `llm_score`: Score suggested by LLM
- `llm_explanation`: LLM's explanation for the score
- `is_approved`: Admin approval status
- `approved_by`: Admin who approved the result
- `approved_at`: Timestamp of approval
- `final_marks`: Final marks after approval

### 3. Backend Changes (`app.py`)
- **Submission Flow**: Students submit → LLM evaluates → Admin reviews → Approval
- **New Routes**:
  - `/admin/pending_evaluations`: List pending evaluations
  - `/admin/review_evaluation/<exam_id>/<student_id>`: Review specific evaluation
  - `/admin/approve_evaluation`: Approve individual scores
  - `/admin/bulk_approve_evaluation`: Bulk approve all scores

### 4. Frontend Updates
- **Admin Interface**:
  - Pending evaluations dashboard
  - Detailed review interface
  - Bulk approval functionality
- **Student Interface**:
  - Pending status display
  - Final results after approval

## Workflow

### Student Submission Process
1. Student completes exam and clicks "Submit"
2. System sends answers to LLM evaluator
3. LLM generates scores and explanations
4. Results stored with `is_approved=False`
5. Student sees "Pending Review" status

### Admin Review Process
1. Admin sees pending evaluations count on dashboard
2. Admin clicks "Pending Reviews" to see all pending evaluations
3. Admin can review individual student evaluations
4. Admin can approve LLM scores or modify them
5. Admin can bulk approve all scores for a student
6. Once approved, students can see final results

## Setup Instructions

### 1. Install Ollama
```bash
# Install Ollama (macOS)
brew install ollama

# Or download from https://ollama.ai/
```

### 2. Start Ollama Service
```bash
ollama serve
```

### 3. Pull Llama 7B Model
```bash
ollama pull llama2:7b
```

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
python app.py
```

## Configuration

### LLM Evaluator Settings
The evaluator can be configured in `llm_evaluator.py`:

```python
evaluator = LLMEvaluator(
    ollama_url="http://localhost:11434",  # Ollama server URL
    model_name="llama2:7b",              # Model to use
    max_retries=3,                       # API retry attempts
    timeout=60                           # Request timeout
)
```

### Evaluation Prompt
The system uses a comprehensive prompt that evaluates answers based on:
- Content Accuracy
- Knowledge Depth
- Completeness
- Clarity
- Relevance

## Testing

### Test LLM Evaluator
```bash
python test_llm_evaluator.py
```

This will test:
- Connection to Ollama
- Model availability
- Sample evaluations
- Error handling

### Manual Testing Workflow
1. Start the application
2. Login as admin and create an exam
3. Login as student and take the exam
4. Submit answers
5. Login as admin and review pending evaluations
6. Approve scores
7. Check student results

## Troubleshooting

### Common Issues

#### 1. LLM Evaluator Not Available
**Error**: "LLM Evaluator not available"
**Solution**: 
- Ensure Ollama is running: `ollama serve`
- Check if model is installed: `ollama list`
- Install model: `ollama pull llama2:7b`

#### 2. Connection Timeout
**Error**: "Failed to get response from Ollama"
**Solution**:
- Check Ollama service status
- Increase timeout in evaluator configuration
- Check network connectivity

#### 3. Model Not Found
**Error**: "Model llama2:7b not found"
**Solution**:
- List available models: `ollama list`
- Pull the model: `ollama pull llama2:7b`
- Or use an available model by updating the configuration

## Performance Considerations

### LLM Response Time
- Typical response time: 5-15 seconds per question
- Depends on system resources and model size
- Consider timeout settings for production use

### Batch Processing
- Each question is evaluated individually
- No batch processing implemented
- Consider implementing for large-scale deployments

## Security Considerations

### API Access
- Ollama runs locally by default
- No external API calls required
- Consider network security for production deployments

### Data Privacy
- All evaluation data stays local
- No data sent to external services
- LLM responses logged for debugging

## Future Enhancements

### Potential Improvements
1. **Batch Evaluation**: Process multiple questions simultaneously
2. **Model Selection**: Allow admin to choose different models
3. **Custom Prompts**: Allow admin to customize evaluation prompts
4. **Performance Metrics**: Track evaluation accuracy and consistency
5. **Auto-approval**: Option to auto-approve scores above certain threshold

### Integration Options
1. **Multiple LLM Providers**: Support for OpenAI, Anthropic, etc.
2. **Model Comparison**: Compare results from different models
3. **Confidence Scoring**: Add confidence levels to evaluations
4. **Feedback Loop**: Learn from admin corrections

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the test script output
3. Check Ollama service status
4. Verify model installation

## Conclusion

The LLM evaluation system provides a more intelligent and transparent approach to answer evaluation. By combining AI-powered assessment with human oversight, it ensures both efficiency and quality in the evaluation process. The system is designed to be flexible, secure, and easy to maintain while providing detailed insights into student performance.
