# AI Setup Guide

This guide will help you configure AI-powered analysis in Lens.

## Overview

Lens supports OpenAI-compatible APIs for enhanced log analysis. You can use:

- **OpenAI** - Official OpenAI API (GPT-4, GPT-3.5)
- **Azure OpenAI** - Microsoft's OpenAI service
- **Local LLMs** - Ollama, LM Studio, or any OpenAI-compatible endpoint

## Quick Start with OpenAI

### 1. Get an API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)

### 2. Configure Lens

**Option A: Using Environment Variables (Recommended)**

Create or edit `.env` file in the `backend` directory:

```bash
# Enable AI features
AI_ENABLED=true

# OpenAI API Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini  # or gpt-4o, gpt-4-turbo, gpt-3.5-turbo
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7
```

**Option B: Using the Settings Dialog**

1. Start Lens
2. Click the Settings icon in the status bar
3. Go to "AI Settings" tab
4. Toggle "Enable AI Processing"
5. Enter your API key
6. Save changes

### 3. Test Connection

In the Settings dialog:
1. Configure your API key
2. Click "Test Connection"
3. Verify you see "Connection successful"

## Azure OpenAI Setup

Azure OpenAI requires a different base URL and API key format.

### Environment Variables

```bash
AI_ENABLED=true
OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2024-02-15-preview
OPENAI_API_KEY=your-azure-api-key
OPENAI_MODEL=gpt-4  # Your deployment name
```

### Settings Dialog

1. Base URL: `https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2024-02-15-preview`
2. API Key: Your Azure OpenAI key
3. Model: Your deployment name (e.g., `gpt-4`)

## Local LLM Setup (Ollama)

Run AI models locally with Ollama for privacy and cost savings.

### 1. Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from https://ollama.com
```

### 2. Pull a Model

```bash
ollama pull llama2
# or
ollama pull codellama
# or
ollama pull mistral
```

### 3. Configure Lens

```bash
AI_ENABLED=true
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama  # Any non-empty value
OPENAI_MODEL=llama2  # Model you pulled
```

## Local LLM Setup (LM Studio)

LM Studio provides a GUI for running local models.

### 1. Install LM Studio

Download from [lmstudio.ai](https://lmstudio.ai)

### 2. Download a Model

1. Open LM Studio
2. Go to "Models" tab
3. Download a model (e.g., `TheBloke/Mistral-7B-Instruct-v0.2-GGUF`)

### 3. Start Local Server

1. Go to "Local Server" tab
2. Select your model
3. Click "Start Server"
4. Note the port (usually 1234)

### 4. Configure Lens

```bash
AI_ENABLED=true
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio  # Any non-empty value
OPENAI_MODEL=local-model  # As shown in LM Studio
```

## Using AI Analysis

### In the UI

1. Run an insight to get results
2. Click "AI Analysis" button below the results
3. Choose analysis type:
   - **Summarize**: Brief overview
   - **Explain**: Detailed analysis
   - **Recommend**: Actionable recommendations
   - **Custom**: Your own prompt
4. Click "Analyze" to stream AI response

### In Config-Based Insights

Add AI configuration to your insight:

```python
INSIGHT_CONFIG = {
    "metadata": {
        "id": "my_insight",
        "name": "My Insight",
        "description": "Analyzes logs"
    },
    "filters": {
        "line_pattern": r"ERROR"
    },
    "ai": {
        "enabled": True,
        "auto": False,  # Set to True for automatic AI analysis
        "prompt_type": "explain",  # or "summarize", "recommend", "custom"
        "prompt": """Custom prompt here..."""  # For custom prompt_type
    }
}
```

### Prompt Variables

Use variables in custom prompts:

```python
"ai": {
    "enabled": True,
    "prompt_type": "custom",
    "prompt": """Analyzed {file_count} files and found {match_count} errors.

Insight: {insight_name}
Description: {insight_description}

Please analyze and provide:
1. Root cause
2. Impact
3. Recommendations

Filtered content:
{result_content}"""
}
```

Available variables:
- `{file_count}` - Number of files analyzed
- `{match_count}` - Number of matches found
- `{insight_name}` - Insight name
- `{insight_description}` - Insight description
- `{result_content}` - Filtered output

## Cost Optimization

### Choose the Right Model

| Model | Cost | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| gpt-4o | $$$$ | Fast | Best | Critical analysis |
| gpt-4o-mini | $$ | Very Fast | Good | General use ⭐ |
| gpt-3.5-turbo | $ | Very Fast | Decent | Quick summaries |
| Local (Ollama) | Free | Medium | Good | Privacy, no cost |

### Reduce Token Usage

1. **Limit content**: Filter logs before AI analysis
2. **Lower max_tokens**: Set to 1000-1500 for summaries
3. **Use summaries**: Use "summarize" instead of "explain"
4. **Local models**: Use Ollama for unlimited usage

### Monitor Usage

- Check your OpenAI dashboard for usage
- Set monthly budget limits in OpenAI account
- Use local models for development/testing

## Security Best Practices

### API Key Management

1. **Never commit** API keys to git
2. **Use environment variables** for production
3. **Rotate keys** periodically
4. **Set usage limits** in OpenAI dashboard

### Data Privacy

1. **Review data** before sending to external APIs
2. **Use local models** for sensitive data
3. **Check terms of service** for your use case
4. **Consider self-hosting** for maximum privacy

## Troubleshooting

### "AI service not configured"

- Check `AI_ENABLED=true` in .env
- Verify `OPENAI_API_KEY` is set
- Restart backend after changing .env

### "Connection test failed"

- Verify API key is correct
- Check base URL format
- Ensure internet connectivity (for OpenAI)
- Check Ollama/LM Studio is running (for local)

### "Rate limit exceeded"

- OpenAI has rate limits per tier
- Wait a few seconds and retry
- Upgrade OpenAI account tier
- Use local models for unlimited access

### Slow responses

- Use gpt-4o-mini or gpt-3.5-turbo
- Reduce max_tokens
- Filter logs to reduce content size
- Consider local models

### "Invalid base URL"

- OpenAI: `https://api.openai.com/v1`
- Azure: `https://{resource}.openai.azure.com/openai/deployments/{deployment}/chat/completions?api-version={version}`
- Ollama: `http://localhost:11434/v1`
- LM Studio: `http://localhost:1234/v1`

## Advanced Configuration

### Custom System Prompts

Edit `backend/app/core/config.py`:

```python
class AIConfig:
    SYSTEM_PROMPTS = {
        "summarize": "Your custom summarize prompt...",
        "explain": "Your custom explain prompt...",
        "recommend": "Your custom recommend prompt...",
    }
```

### Per-Insight Model Override

```python
"ai": {
    "enabled": True,
    "model": "gpt-4o",  # Override global model for this insight
    "max_tokens": 3000,  # Override global max_tokens
    "temperature": 0.5   # Override global temperature
}
```

## Support

For issues or questions:
- Check GitHub Issues
- Read the [Features Documentation](../FEATURES.md)
- Review insight examples in `backend/app/insights/`

## Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Ollama Documentation](https://ollama.com/docs)
- [LM Studio](https://lmstudio.ai)

