# Perplexity Sonar Deep Research Integration

## Overview
The research mode in Omnix AI has been upgraded to use **Perplexity's Sonar Deep Research API**, replacing the previous custom research implementation. This provides more accurate, comprehensive, and faster research capabilities.

## Features
- **Deep Research**: Automatically performs dozens of searches and reads hundreds of sources
- **Fast Results**: Most research tasks complete in under 3 minutes
- **Comprehensive Analysis**: Includes citations, key insights, and source verification
- **Multi-domain Support**: Finance, technology, health, current events, and more
- **Source Attribution**: Every answer includes numbered sources with direct links

## Setup

### 1. Get Your Perplexity API Key
1. Visit [Perplexity AI](https://www.perplexity.ai/)
2. Sign up for an account or log in
3. Navigate to API settings
4. Generate an API key

### 2. Configure Environment
Add your API key to the `.env` file:
```env
PERPLEXITY_API_KEY=your_actual_perplexity_api_key_here
```

### 3. Test the Integration
Run the test script to verify everything is working:
```bash
python test_perplexity.py
```

## API Endpoints

### Research Endpoint
**POST** `/research`
```json
{
    "query": "Your research question here"
}
```

**Response:**
```json
{
    "summary": "Comprehensive research summary...",
    "sources": [
        {
            "title": "Source Title",
            "url": "https://...",
            "snippet": "Relevant excerpt...",
            "credibility": 0.9
        }
    ],
    "insights": ["Key insight 1", "Key insight 2", ...],
    "confidence": 0.95,
    "source_count": 25,
    "metadata": {
        "total_tokens": 5000,
        "search_queries_performed": 30,
        "sources_analyzed": 150
    }
}
```

### Enhanced Research Endpoint
**POST** `/enhanced_research`
```json
{
    "query": "Your research question",
    "type": "comprehensive"  // Options: comprehensive, fact_check, comparative
}
```

## Pricing
- **Input Tokens**: $2 per 1M tokens
- **Output Tokens**: $8 per 1M tokens
- **Citation Tokens**: $2 per 1M tokens
- **Search Queries**: $5 per 1K requests
- **Reasoning Tokens**: $3 per 1M tokens

Example: A typical research request that performs 30 searches costs approximately $0.15

## Frontend Integration
The frontend automatically detects and uses the Perplexity integration when available. The research mode UI remains the same, but results are now powered by Perplexity's advanced AI.

## Fallback Behavior
If the Perplexity API key is not configured, the system will fall back to basic research using:
- Brave Search API for web results
- Gemini for content synthesis

## Advantages Over Previous System
1. **Better Accuracy**: Professional-grade research with verified sources
2. **Faster Performance**: 3-minute average vs 5-10 minutes previously
3. **More Sources**: Analyzes hundreds of sources automatically
4. **Built-in Fact-Checking**: Automatic verification of claims
5. **Lower Maintenance**: No need to maintain custom research logic

## Troubleshooting

### API Key Not Working
- Verify the key is correctly copied to `.env`
- Check your Perplexity account for API access
- Ensure you have sufficient API credits

### Research Failing
- Check the Flask server logs for detailed error messages
- Run `python test_perplexity.py` to test the integration
- Verify your internet connection

### Slow Performance
- Perplexity typically completes in 3 minutes
- Complex queries may take longer
- Check your API rate limits

## Migration Notes
- The old `enhanced_research_mode.py` is no longer used
- All research endpoints now use Perplexity
- Previous research cache is not compatible (new cache format)
- Frontend remains fully compatible

## Support
For Perplexity API issues: https://docs.perplexity.ai/
For integration issues: Check the Flask server logs or run the test script