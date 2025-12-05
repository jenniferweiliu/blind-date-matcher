# USC Blind Date Matcher - Groq AI Version (FREE!)

This version uses **Groq AI** to intelligently evaluate compatibility between students, providing nuanced reasoning and analysis - completely FREE!

## Key Differences from Algorithmic Version

| Feature | Algorithmic (`matcher.py`) | Groq API (`matcher_api.py`) |
|---------|---------------------------|-------------------------------|
| **Matching Method** | Mathematical scoring algorithm | AI reasoning and analysis |
| **Speed** | Fast (~1 second) | Fast (~2-5 min for 50 people) |
| **Cost** | Free | **FREE** (Groq's free tier) |
| **Insights** | Compatibility score only | Score + reasoning + concerns |
| **Customization** | Change code weights | Adjust AI prompt |
| **Understanding** | Pattern matching | Deep contextual analysis |

## How It Works

1. **Loads** form responses
2. **(Optional) Fetches LinkedIn data** for each person - experience, education, skills
3. **Filters** by orientation/gender compatibility
4. **Sends each pair** to Groq API with full profile details + LinkedIn data
5. **Groq AI analyzes** personalities, values, lifestyles, descriptions, AND professional backgrounds
6. **Returns** compatibility score (0-100) + reasoning
7. **Creates optimal matches** using maximum weight matching
8. **Exports** to CSV with AI insights

## 🔗 LinkedIn Integration (NEW!)

The matcher can now extract and use LinkedIn profile data for even more intelligent matching!

### What It Adds:
- **Professional background** - current role, company, past experience
- **Education** - degree, field of study, university
- **Skills** - technical skills, soft skills
- **Career trajectory** - ambition indicators, industry focus

### Why It Helps:
- Match people with similar career interests
- Find compatible ambition levels beyond self-reported data
- Identify shared professional networks or industries
- Better understand someone's true interests and expertise

### Example:
> Person A: Works at Google, studied CS, skills include Python, Machine Learning
> Person B: Works at Meta, studied CS, skills include JavaScript, AI
> **Groq AI**: "Both are in tech with AI interests - great conversation starters!"

## Setup

### 0. Update Google Form (for LinkedIn)

If you want to use LinkedIn integration, add this question to your Google Form:

**Question:** LinkedIn URL (optional)
**Type:** Short answer
**Description:** "Your LinkedIn profile URL (e.g., https://linkedin.com/in/yourname)"

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Get Free Groq API Key

1. Sign up at **https://console.groq.com** (NO CREDIT CARD REQUIRED!)
2. Go to API Keys section
3. Create a new API key
4. Copy the key

### 3. Set Environment Variables

```bash
# Required: Groq API (FREE!)
export GROQ_API_KEY='your-groq-api-key-here'

# Optional: LinkedIn (for enhanced matching)
export LINKEDIN_EMAIL='your-linkedin-email@example.com'
export LINKEDIN_PASSWORD='your-linkedin-password'
```

**⚠️ Important LinkedIn Notes:**
- This uses unofficial LinkedIn scraping via `linkedin-api` library
- **Against LinkedIn ToS** - use at your own risk
- For personal/educational use only
- May trigger LinkedIn security alerts (use a dedicated account)
- Rate limited - be patient with large batches
- Works without LinkedIn too (just won't include professional data)

## Usage

### Basic (without LinkedIn):
```bash
python3 matcher_api.py responses.csv
```

### With LinkedIn Integration:
```bash
# Set credentials first
export LINKEDIN_EMAIL='your-email@example.com'
export LINKEDIN_PASSWORD='your-password'

# Run matcher
python3 matcher_api.py responses.csv
```

### Sample Output

```
USC Blind Date Matcher - Groq AI Version (FREE) with LinkedIn
==================================================

Loading responses from responses.csv...
Loaded 50 responses

Evaluating compatibility for 50 people using Groq AI...
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

🎉 **COMPLETELY FREE!**

- **Model**: Llama 3.1 70B (`llama-3.1-70b-versatile`)
- **Cost**: **$0.00** - Groq offers generous free tier
- **Rate Limits**: Very generous for personal projects
- **No credit card required** to sign up!

This means you can run the matcher as many times as you want without worrying about costs!

## Advantages of Groq AI Version

### 1. **Nuanced Understanding**
Groq AI understands context that algorithms miss:
- "Loves adventure" matches with "Spontaneous and outdoorsy"
- "Homebody" recognized as incompatible with "I'm out every night"
- Subtle personality cues in free-text descriptions

### 2. **Reasoning Transparency**
Every match includes AI's explanation:
> "Both value intellectual conversations and share a love for reading. Their calm,
> introverted personalities complement each other well."

### 3. **Adaptive Matching**
Groq AI can:
- Identify deal-breakers beyond the checklist
- Recognize complementary vs. similar traits
- Balance "opposites attract" vs. "birds of a feather"

### 4. **No Manual Tuning**
The algorithmic version requires tweaking weights. Groq AI adapts naturally.

### 5. **FREE & FAST**
Groq is known for incredibly fast inference speeds - you get AI-powered matching without any cost!

## When to Use Which Version?

**Use Algorithmic (`matcher.py`) when:**
- You want instant results (< 1 second)
- You prefer a completely offline solution
- You're working in an environment without internet access

**Use Groq API (`matcher_api.py`) when:**
- You want AI-powered matching with explanations
- You want to understand WHY people match
- You have rich, detailed responses to analyze
- You want the best quality matches
- **Recommended for most users** - it's FREE and provides much better insights!

## Customizing the Matching Logic

Edit the prompt in `matcher_api.py` to change how Groq AI evaluates:

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

**"GROQ_API_KEY not set"**
- Run: `export GROQ_API_KEY='your-key'`
- Or add to `~/.bashrc` or `~/.zshrc` for persistence
- Get your FREE key at: https://console.groq.com/keys

**API rate limits**
- Groq has generous rate limits for the free tier
- If you hit limits, wait a minute and try again
- See: https://console.groq.com/docs/rate-limits

**Want to try different models?**
- Edit line 272 in `matcher_api.py` to change the model
- Options: `llama-3.1-70b-versatile`, `mixtral-8x7b-32768`, `llama-3.1-8b-instant`
- All models are FREE on Groq!

## Comparing Results

Run both versions and compare:

```bash
# Algorithmic version
python3 matcher.py responses.csv
# Output: matches.csv

# Groq AI version
python3 matcher_api.py responses.csv
# Output: matches_api.csv
```

Often the top matches overlap, but Groq AI finds subtle compatibilities the algorithm misses!
