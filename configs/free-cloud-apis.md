# Free Cloud AI APIs — Supplement Your Local Models

Use these when you need more power than your local 8B models can provide.

## Tier 1: Most Generous Free Tiers

### Groq (Fastest inference)
- **Free:** 1,000-14,400 req/day depending on model
- **Models:** Llama 3.3 70B, DeepSeek R1, Qwen QwQ
- **Speed:** 500+ tok/s (fastest API available)
- **Setup:** https://console.groq.com → Get API key
- **OpenWebUI:** Settings > Providers > Add OpenAI-compatible
  - URL: https://api.groq.com/openai/v1
  - Key: your-groq-key

### Google AI Studio (Gemini)
- **Free:** 250K tokens/min, generous daily limits
- **Models:** Gemini 2.5 Flash, Gemma
- **Setup:** https://aistudio.google.com → Get API key
- **OpenWebUI:** Settings > Providers > Add OpenAI-compatible
  - URL: https://generativelanguage.googleapis.com/v1beta/openai
  - Key: your-google-key

### Mistral (La Plateforme)
- **Free:** 1 BILLION tokens/month at 1 req/sec
- **Models:** Mistral Large, Codestral, Mistral Small
- **Setup:** https://console.mistral.ai → Get API key
- **OpenWebUI:** Settings > Providers > Add OpenAI-compatible
  - URL: https://api.mistral.ai/v1
  - Key: your-mistral-key

## Tier 2: Useful Supplements

### OpenRouter (Aggregator)
- **Free:** 20 req/min on free models
- **Models:** Many open-source models hosted free
- **Setup:** https://openrouter.ai → Get API key
- **Note:** $10 lifetime topup unlocks 1,000 req/day

### Hugging Face Inference API
- **Free:** Moderate rate limits, no credit card
- **Models:** Wide selection
- **Setup:** https://huggingface.co/settings/tokens

## Strategy

1. **Daily driver:** Local deepseek-r1:8b and qwen3:8b (private, no limits)
2. **Heavy reasoning:** Groq (DeepSeek R1 70B) when local isn't enough
3. **Long documents:** Google AI Studio (Gemini Flash, huge context)
4. **Coding marathon:** Mistral (Codestral, 1B tokens/month free)
5. **Fallback:** OpenRouter for anything else

## Reference
Community-maintained list of all free APIs:
https://github.com/cheahjs/free-llm-api-resources
