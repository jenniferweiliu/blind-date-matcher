# USC Blind Date Matcher

Algorithmic matchmaking for USC students based on compatibility scores.

## How It Works

The matcher uses a **maximum weight matching algorithm** to create optimal one-to-one pairings based on:

- **Gender & interested in** compatibility (uses explicit "I'm interested in" responses)
- **Trait matching** - matches what people want with who their partner actually is
- Social preferences (introvert/extrovert, party habits)
- Shared interests and hobbies
- Lifestyle compatibility (drinking, weed, ambition)
- Date preferences
- Deal-breakers

Each pair gets a **compatibility score (0-100%)** based on how well they match.

## Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Export Google Form Responses

1. Open your Google Form
2. Click the **"Responses"** tab
3. Click the green **spreadsheet icon** (top right) to create a Google Sheet
4. In the Google Sheet: **File > Download > Comma Separated Values (.csv)**
5. Save the file (e.g., `responses.csv`)

## Usage

Run the matcher with your CSV file:

```bash
python matcher.py responses.csv
```

### Output

The script will:
1. Load all responses
2. Filter compatible pairs (based on orientation/gender)
3. Calculate compatibility scores
4. Find optimal matches
5. Export results to `matches.csv`
6. Display top 10 matches in terminal

### Example Output

```
USC Blind Date Matcher
==================================================

Loading responses from responses.csv...
Loaded 50 responses

Finding optimal matches...
Calculating compatibility for 50 people...
Found 423 compatible pairs

Found 24 matches!
2 people unmatched

Matches exported to matches.csv

==================================================
TOP MATCHES:
==================================================

Match #1: 87.3%
  John Smith + Jane Doe
  Shared interests: Music, Cooking/baking, Binge-watching shows

Match #2: 84.1%
  Alex Johnson + Sam Lee
  Shared interests: Sports/working out, Gaming
```

## Output File (matches.csv)

The CSV includes:
- Person 1 Name & Email
- Person 2 Name & Email
- Compatibility Score
- Shared Hobbies
- What each person is looking for

## Compatibility Scoring Breakdown

| Factor | Max Points | Description |
|--------|-----------|-------------|
| Shared Hobbies | 20 | Common interests (weighted by importance) |
| Social Battery | 15 | Similar introversion/extroversion levels |
| Trait Matching | 15 | What they want matches who you are (e.g., they want humor, you're funny) |
| **Text Similarity (AI)** | **10** | **Semantic matching of type descriptions using NLP** |
| Ambition Level | 10 | Compatible career/life goals |
| Friday Night Style | 10 | Similar weekend preferences |
| Dream Date | 10 | Matching ideal date activities |
| Drinking Habits | 10 | Similar drinking preferences |
| Partner Values | 5 | Similar values in what they seek |
| Weed | 5 | Matching weed preferences |
| **TOTAL** | **100** | |

## How It Works

### 🤖 AI-Powered Text Similarity (NEW!)

The matcher uses **sentence-transformers** (a neural network) to analyze the "Describe your type" text responses and match them with people's actual traits and hobbies.

**How it works:**
1. Person A describes their ideal type: *"Smart and kind girl who enjoys gaming books and Netflix"*
2. Person B's profile says: Traits: *"Smart, Kind, Chill"* | Hobbies: *"Gaming, Reading, Binge-watching"*
3. The AI calculates semantic similarity between what A wants and who B actually is
4. Does the same for B→A
5. Awards up to 10 compatibility points

**Why this is powerful:**
- Understands synonyms ("athletic" = "fit", "nerdy" = "intellectual")
- Captures nuance in natural language
- Matches beyond just keywords

**Example:** Sarah wants *"Tall and funny guy who enjoys good food and music"* → Gets matched with Alex who is *"Funny, Adventurous, Kind"* with hobbies *"Music, Cooking"* → High semantic similarity!

**The model:** Uses `all-MiniLM-L6-v2` - a lightweight but accurate transformer model (~80MB, runs locally).

---

### How Trait Matching Works
The matcher intelligently maps what people value in a partner to actual personality traits:

**Trait → Value Mapping:**
- Funny → Sense of humor
- Smart → Smart/intellectual
- Hardworking/Ambitious/driven → Ambition/has goals
- Adventurous → Adventurous
- Kind/caring → Kind/caring
- Life of the party/Spontaneous → Fun/spontaneous
- Reliable/loyal → Good communicator

**Example:** If Person A values "Sense of humor" and Person B's friends describe them as "Funny," they get bonus compatibility points!

---

## Notes & Limitations

### Deal-breakers
Currently only "Smoker" is enforced (matches with weed usage).

"Bad communicator" is listed but not checked (no communication question in form).

### Unmatched People
If there's an odd number of compatible people, one person won't get matched. The algorithm prioritizes maximizing overall compatibility, not ensuring everyone gets a match.

## Customization

### Adjust Scoring Weights

Edit `calculate_compatibility_score()` in `matcher.py` to change point values:

```python
# Example: Make shared hobbies more important
hobby_score = (shared_hobbies / 3) * 35  # Changed from 25 to 35
```

### Add New Compatibility Factors

Add new scoring logic in `calculate_compatibility_score()`:

```python
# Example: Year in school compatibility
if person1.get('year') == person2.get('year'):
    score += 5
```

### Change Matching Algorithm

The script uses `networkx.max_weight_matching()` which maximizes total compatibility across all pairs.

To prioritize matching everyone (even with lower scores), change:
```python
matching = nx.max_weight_matching(G, maxcardinality=True)  # Changed False to True
```

## Troubleshooting

**"No module named pandas"**
- Run: `pip install -r requirements.txt`

**"FileNotFoundError"**
- Make sure you're running the script from the `blind-date` folder
- Check that your CSV filename matches what you typed

**"KeyError" or column errors**
- Make sure your CSV is exported directly from Google Forms
- Don't rename any columns in the spreadsheet before exporting

**Very low compatibility scores**
- This is normal if people have very different preferences
- You can lower the threshold or adjust weights to be more lenient

## Recent Updates ✨

- [x] **AI-powered text similarity** - Uses NLP to semantically match "type" descriptions with actual profiles
- [x] Added "How would your friends describe you?" question to form
- [x] Implemented trait matching - matches self-description with partner values
- [x] Added explicit "I'm interested in" question for accurate orientation matching
- [x] Fixed orientation compatibility to properly respect gender preferences

## Future Improvements

- [ ] Weight matches by "What are you looking for?" (serious vs casual)
- [ ] Export to Excel with formatting instead of CSV
- [ ] Generate personalized match explanations ("You both love concerts!")
- [ ] Add visualization/analytics dashboard
- [ ] Support for polyamorous/non-monogamous matching preferences
