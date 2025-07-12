# AI Provider Configuration

This application supports multiple AI providers for generating workout recommendations. You can use either OpenAI or Claude (Anthropic), or let the system automatically detect which one is available.

## Quick Setup

1. Choose your AI provider by setting `AI_PROVIDER` in your `.env` file:
   - `AI_PROVIDER=openai` - Use OpenAI exclusively
   - `AI_PROVIDER=claude` - Use Claude exclusively  
   - `AI_PROVIDER=auto` - Automatically use whichever is configured (default)

2. Configure your chosen provider(s):

### OpenAI Setup
```env
OPENAI_API_KEY=your_openai_api_key_here
```
Get your API key from: https://platform.openai.com/api-keys

### Claude Setup
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```
Get your API key from: https://console.anthropic.com/settings/keys

## Auto Mode

When `AI_PROVIDER=auto` (or not set), the system will:
1. First try Claude if configured
2. Fall back to OpenAI if Claude is not available
3. Show an error if neither is configured

This is useful when one service is down - just configure both and the system will use whichever is available.

## Switching Providers

You can switch providers at any time by:
1. Updating the `AI_PROVIDER` setting in `.env`
2. Restarting the web server

No other changes are needed - the recommendation engine will automatically use the new provider.

## Cost Comparison

Both providers use usage-based pricing:
- **OpenAI**: ~$5-10/month for typical usage
- **Claude**: Similar pricing, often slightly cheaper for comparable models

## Provider Differences

Both providers generate high-quality workout recommendations. Minor differences:
- **Claude**: Often provides more detailed explanations and reasoning
- **OpenAI**: Sometimes faster response times

The recommendation quality is excellent with either provider.