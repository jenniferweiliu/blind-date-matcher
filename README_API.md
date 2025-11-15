# USC Blind Date Matcher - Claude API Version

This version uses **Claude AI** to intelligently evaluate compatibility between students, providing nuanced reasoning and analysis.

## Key Differences from Algorithmic Version

| Feature | Algorithmic (`matcher.py`) | Claude API (`matcher_api.py`) |
|---------|---------------------------|-------------------------------|
| **Matching Method** | Mathematical scoring algorithm | AI reasoning and analysis |
| **Speed** | Fast (~1 second) | Slower (~5-10 min for 50 people) |
| **Cost** | Free | ~$0.50-2.00 per run (API costs) |
| **Insights** | Compatibility score only | Score + reasoning + concerns |
| **Customization** | Change code weights | Adjust AI prompt |
| **Understanding** | Pattern matching | Deep contextual analysis |

## How It Works

1. **Loads** form responses
2. **Filters** by orientation/gender compatibility
3. **Sends each pair** to Claude API with full profile details
4. **Claude analyzes** personalities, values, lifestyles, and descriptions
5. **Returns** compatibility score (0-100) + reasoning
6. **Creates optimal matches** using maximum weight matching
7. **Exports** to CSV with AI insights

## Setup

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Get Anthropic API Key

1. Sign up at https://console.anthropic.com
2. Go to API Keys section
3. Create a new API key
4. Copy the key

### 3. Set Environment Variable

```bash
# On Mac/Linux
export ANTHROPIC_API_KEY='your-api-key-here'

# On Windows (PowerShell)
$env:ANTHROPIC_API_KEY='your-api-key-here'
```

## Usage

```bash
python3 matcher_api.py responses.csv
```

### Sample Output

```
USC Blind Date Matcher - Claude API Version
==================================================

Loading responses from responses.csv...
Loaded 50 responses

Evaluating compatibility for 50 people using Claude API...
This may take a few minutes...

Evaluating pair 1: Alex Johnson + Sarah Mitchell... Score: 87%
Evaluating pair 2: Mike Chen + Emma Davis... Score: 92%
...

Found 324 compatible pairs

Found 24 matches!
2 people unmatched

Matches exported to matches_api.csv

==================================================
TOP MATCHES:
==================================================

Match #1: 92%
  Mike Chen + Emma Davis
  Reasoning: Both are highly social, ambitious, and love partying. Their energetic
  personalities and shared goals make them an excellent match.
  Shared interests: Going to parties/bars, Sports/working out
```

## Output File (matches_api.csv)

The CSV includes:
- Person 1 & 2 Names and Emails
- Compatibility Score
- **AI Reasoning** (why they match)
- Shared Interests
- Key Matches (what makes them compatible)
- Potential Concerns (if any)
- What each is looking for

## Cost Estimation

- **Model**: Claude Sonnet 4 (`claude-sonnet-4-20250514`)
- **Cost**: ~$3 per million input tokens, ~$15 per million output tokens
- **Per pair evaluation**: ~500 input + 200 output tokens = ~$0.004 per pair
- **For 50 people**: ~1,225 pairs × $0.004 = **~$4.90 total**

For smaller groups (<20 people), cost is usually **under $1**.

## Advantages of Claude API Version

### 1. **Nuanced Understanding**
Claude understands context that algorithms miss:
- "Loves adventure" matches with "Spontaneous and outdoorsy"
- "Homebody" recognized as incompatible with "I'm out every night"
- Subtle personality cues in free-text descriptions

### 2. **Reasoning Transparency**
Every match includes Claude's explanation:
> "Both value intellectual conversations and share a love for reading. Their calm,
> introverted personalities complement each other well."

### 3. **Adaptive Matching**
Claude can:
- Identify deal-breakers beyond the checklist
- Recognize complementary vs. similar traits
- Balance "opposites attract" vs. "birds of a feather"

### 4. **No Manual Tuning**
The algorithmic version requires tweaking weights. Claude adapts naturally.

## When to Use Which Version?

**Use Algorithmic (`matcher.py`) when:**
- You want instant results
- Running frequently / testing
- Budget is a concern
- You have 100+ people (API would be expensive)

**Use Claude API (`matcher_api.py`) when:**
- Quality > speed
- You want explanations for matches
- You have rich, detailed responses
- Budget allows ($1-5 per run)
- Final, production matching for an event

## Customizing the Matching Logic

Edit the prompt in `matcher_api.py` to change how Claude evaluates:

```python
prompt = f"""You are an expert matchmaker...

Please analyze their compatibility focusing on:
1. Long-term relationship potential  # <-- Add your criteria
2. Shared life goals
3. Complementary personalities
...
"""
```

## Troubleshooting

**"ANTHROPIC_API_KEY not set"**
- Run: `export ANTHROPIC_API_KEY='your-key'`
- Or add to `~/.bashrc` or `~/.zshrc` for persistence

**API rate limits**
- Claude has rate limits; for large batches, add delays
- See: https://docs.anthropic.com/en/api/rate-limits

**High costs**
- Test with small sample first (`head -n 10 responses.csv > test.csv`)
- Use cheaper model like `claude-haiku-3-20240307` (edit script)

## Comparing Results

Run both versions and compare:

```bash
# Algorithmic version
python3 matcher.py responses.csv
# Output: matches.csv

# Claude API version
python3 matcher_api.py responses.csv
# Output: matches_api.csv
```

Often the top matches overlap, but Claude finds subtle compatibilities the algorithm misses!
