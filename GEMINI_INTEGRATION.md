# Gemini Integration Example

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Gemini API Key:**
   - Visit https://aistudio.google.com/
   - Create a new API key
   - Set environment variable: `export GEMINI_API_KEY='your-key'`

3. **Optional: Set OpenAI API Key (fallback):**
   ```bash
   export OPENAI_API_KEY='your-openai-key'
   ```

## Usage

The chatbot now supports Google Gemini with the following priority:

1. **Gemini** (if available)
2. **OpenAI** (if Gemini fails)
3. **Template-based answers** (if both LLMs fail)

## Example

```python
from chatbot import MutualFundChatbot

# Initialize chatbot (will automatically use Gemini if available)
chatbot = MutualFundChatbot()

# Check which LLM is available
print(f"Gemini available: {chatbot.gemini_model is not None}")
print(f"OpenAI available: {chatbot.openai_client is not None}")

# Ask a question
response = chatbot.answer_question("What is the expense ratio of HDFC Flexi Cap Fund?")
print(response['answer'])
```

## Testing

Run the integration test:
```bash
python3 test_gemini_integration.py
```

## Features

- **Automatic LLM selection**: Gemini is tried first, then OpenAI
- **Graceful fallback**: Works without any API keys using templates
- **Same interface**: No changes needed to existing code
- **Error handling**: Failed LLM calls automatically fall back to the next option
