"""
USC Blind Date Matcher - Free AI Version with LinkedIn Integration
Uses Groq AI (free) to intelligently match students based on comprehensive profile analysis,
including data extracted from LinkedIn profiles.

IMPORTANT: This uses unofficial LinkedIn scraping. Use responsibly and at your own risk.
Consider LinkedIn's Terms of Service before using in production.
"""

import pandas as pd
from groq import Groq
import os
import sys
import json
import networkx as nx
from typing import Dict, List, Tuple, Optional
from linkedin_api import Linkedin
import time


def load_responses(csv_file):
    """Load Google Form responses from CSV file."""
    df = pd.read_csv(csv_file)

    # Rename columns to simpler names for easier access
    column_mapping = {
        'Timestamp': 'timestamp',
        'Name (first and last)': 'name',
        'Email': 'email',
        'Phone Number': 'phone',
        'LinkedIn Url (algorithm will scrape your profile)': 'linkedin_url',
        'Gender': 'gender',
        'Sexual Orientation': 'orientation',
        'I\'m interested in': 'interested_in',
        'Year in school': 'year',
        'What are you looking for?': 'looking_for',
        'My social battery is...': 'social_battery',
        'On a Friday night you\'ll find me..': 'friday_night',
        'My fav social media': 'social_media',
        'How would your friends describe you? (pick top 3)': 'self_traits',
        'What do you do for fun? (top 3)': 'hobbies',
        'Dream date activity?': 'dream_date',
        'Favorite tv show/movie': 'favorite_media',
        'Drinking': 'drinking',
        'Weed': 'weed',
        'What matters most in a partner? (Pick your top 3)': 'partner_values',
        'How important is it that they share your interests/hobbies? (Scale 1-5)': 'shared_interests_importance',
        'Describe your type (qualities, physical type, etc.)': 'type_description',
        'Ideal career/ambition level in your blind date': 'ambition',
        'Deal-breakers?': 'dealbreakers',
        'Fun fact about yourself': 'fun_fact'
    }

    df = df.rename(columns=column_mapping)
    return df


def extract_linkedin_username(linkedin_url):
    """Extract LinkedIn username from URL."""
    if not linkedin_url or pd.isna(linkedin_url):
        return None

    # Handle different LinkedIn URL formats
    # https://www.linkedin.com/in/username/
    # linkedin.com/in/username
    url = str(linkedin_url).strip()

    if '/in/' in url:
        username = url.split('/in/')[1].strip('/')
        # Remove any query parameters
        username = username.split('?')[0]
        return username

    return None


def get_linkedin_data(linkedin_client: Optional[Linkedin], linkedin_url: str) -> Optional[Dict]:
    """
    Extract data from LinkedIn profile.
    Returns dict with experience, education, skills, etc.
    """
    if not linkedin_client or not linkedin_url:
        return None

    try:
        username = extract_linkedin_username(linkedin_url)
        if not username:
            return None

        print(f"    Fetching LinkedIn data for {username}...", end=" ")

        # Get profile data
        profile = linkedin_client.get_profile(username)

        # Extract relevant information
        linkedin_data = {
            'headline': profile.get('headline', ''),
            'summary': profile.get('summary', ''),
            'experience': [],
            'education': [],
            'skills': []
        }

        # Extract experience
        experiences = profile.get('experience', [])
        for exp in experiences[:3]:  # Top 3 experiences
            linkedin_data['experience'].append({
                'title': exp.get('title', ''),
                'company': exp.get('companyName', ''),
                'description': exp.get('description', '')
            })

        # Extract education
        educations = profile.get('education', [])
        for edu in educations:
            linkedin_data['education'].append({
                'school': edu.get('schoolName', ''),
                'degree': edu.get('degreeName', ''),
                'field': edu.get('fieldOfStudy', '')
            })

        # Extract skills
        skills = profile.get('skills', [])
        linkedin_data['skills'] = [skill.get('name', '') for skill in skills[:10]]  # Top 10 skills

        print("✓")

        # Add small delay to avoid rate limiting
        time.sleep(1)

        return linkedin_data

    except Exception as e:
        print(f"✗ (Error: {str(e)})")
        return None


def is_compatible_orientation(person1, person2):
    """Check if two people are compatible based on gender and interested in."""
    gender1 = str(person1.get('gender', '')).lower().strip()
    gender2 = str(person2.get('gender', '')).lower().strip()

    interested1_raw = str(person1.get('interested_in', '')).lower()
    interested2_raw = str(person2.get('interested_in', '')).lower()

    interested1 = [x.strip() for x in interested1_raw.split(',')]
    interested2 = [x.strip() for x in interested2_raw.split(',')]

    # Check if person1 is interested in person2's gender
    person1_interested = False
    if 'men' in interested1 and gender2 == 'man':
        person1_interested = True
    elif 'women' in interested1 and gender2 == 'woman':
        person1_interested = True
    elif 'other' in interested1 and (gender2 == 'non-binary' or gender2 == 'other'):
        person1_interested = True

    if not person1_interested:
        return False

    # Check if person2 is interested in person1's gender
    person2_interested = False
    if 'men' in interested2 and gender1 == 'man':
        person2_interested = True
    elif 'women' in interested2 and gender1 == 'woman':
        person2_interested = True
    elif 'other' in interested2 and (gender1 == 'non-binary' or gender1 == 'other'):
        person2_interested = True

    if not person2_interested:
        return False

    return True


def create_person_profile(person):
    """Create a readable profile string for Claude to analyze."""
    profile = f"""
Name: {person['name']}
Gender: {person.get('gender', 'N/A')}
Sexual Orientation: {person.get('orientation', 'N/A')}
Year: {person.get('year', 'N/A')}
Looking for: {person.get('looking_for', 'N/A')}

Personality Traits: {person.get('self_traits', 'N/A')}
Social Battery: {person.get('social_battery', 'N/A')}
Friday Nights: {person.get('friday_night', 'N/A')}
Favorite Social Media: {person.get('social_media', 'N/A')}
Hobbies: {person.get('hobbies', 'N/A')}
Dream Date: {person.get('dream_date', 'N/A')}

Lifestyle:
- Drinking: {person.get('drinking', 'N/A')}
- Weed: {person.get('weed', 'N/A')}
- Ambition: {person.get('ambition', 'N/A')}

What they value in a partner: {person.get('partner_values', 'N/A')}
Shared interests importance (1-5): {person.get('shared_interests_importance', 'N/A')}
Their type: {person.get('type_description', 'N/A')}
Deal-breakers: {person.get('dealbreakers', 'N/A')}

Favorite TV/Movie: {person.get('favorite_media', 'N/A')}
Fun fact: {person.get('fun_fact', 'N/A')}
""".strip()

    # Add LinkedIn data if available
    linkedin_data = person.get('linkedin_data')
    if linkedin_data:
        profile += "\n\nLINKEDIN PROFILE DATA:"

        if linkedin_data.get('headline'):
            profile += f"\nHeadline: {linkedin_data['headline']}"

        if linkedin_data.get('summary'):
            profile += f"\nSummary: {linkedin_data['summary'][:200]}..."  # Truncate long summaries

        if linkedin_data.get('experience'):
            profile += "\nExperience:"
            for exp in linkedin_data['experience']:
                if exp.get('title') and exp.get('company'):
                    profile += f"\n  - {exp['title']} at {exp['company']}"

        if linkedin_data.get('education'):
            profile += "\nEducation:"
            for edu in linkedin_data['education']:
                parts = []
                if edu.get('degree'):
                    parts.append(edu['degree'])
                if edu.get('field'):
                    parts.append(edu['field'])
                if edu.get('school'):
                    parts.append(f"at {edu['school']}")
                if parts:
                    profile += f"\n  - {' '.join(parts)}"

        if linkedin_data.get('skills'):
            profile += f"\nTop Skills: {', '.join(linkedin_data['skills'][:10])}"

    return profile


def evaluate_compatibility_with_groq(person1, person2, client):
    """
    Use Groq API to evaluate compatibility between two people.
    Returns a compatibility score (0-100) and reasoning.
    """
    profile1 = create_person_profile(person1)
    profile2 = create_person_profile(person2)

    prompt = f"""You are an expert matchmaker analyzing compatibility between two USC students for a blind date matching program.

Context:
- "The Vic" refers to a popular social bar in downtown Los Angeles. If mentioned in profiles, it indicates nightlife/social preferences.
- When analyzing LinkedIn data, infer traits: sports teams → athletic, internships → driven/ambitious, non-profit work → kind/compassionate

Here are their profiles:

PERSON A:
{profile1}

PERSON B:
{profile2}

Please analyze their compatibility across these dimensions:

1. **Personality & Trait Compatibility**:
   - Compare their personality traits (self_traits)
   - Assess if their traits complement each other or create balance
   - Social battery alignment - do their energy levels match?
   - Favorite social media can indicate personality (TikTok/Instagram = visual/social, LinkedIn = professional, etc.)
   - Consider sexual orientation context for understanding their identity and experiences

2. **Shared Interests and Hobbies** - **IMPORTANT**: Weight this based on each person's "Shared interests importance" rating (1-5):
   - If someone rates it 4-5, shared interests should be heavily weighted for their compatibility
   - If someone rates it 1-2, lack of shared interests shouldn't hurt the score much
   - Consider if there's a mismatch in how important each person thinks shared interests are
   - Look for overlapping hobbies and activities

3. **Type Description Matching** - **CRITICAL**:
   - Check if Person A's "Their type" description matches Person B's actual profile (traits, hobbies, physical attributes, personality)
   - Check if Person B's "Their type" description matches Person A's actual profile
   - This is bidirectional - both people should somewhat match what the other is looking for
   - Significant mismatches here should notably impact the score

4. **Partner Values Alignment** - **CRITICAL**:
   - Check if what Person A values in a partner (partner_values) actually exists in Person B
   - Check if what Person B values in a partner actually exists in Person A
   - Examples: If someone values "athletic" does the other person play sports/work out? If someone values "ambitious" does the other show ambition in their profile/LinkedIn?
   - Use LinkedIn data to verify these values (sports teams = athletic, internships = ambitious, non-profits = kind)

5. **Lifestyle Compatibility**:
   - Drinking habits alignment (similar levels or compatible differences)
   - Weed usage alignment
   - Ambition/career level compatibility
   - Social habits and energy levels

6. **Friday Night & Dream Date Compatibility**:
   - Are their typical Friday nights compatible? (partying vs staying in vs somewhere in between)
   - Are their dream dates compatible or complementary?
   - Can their ideal activities coexist or do they conflict?

7. **Relationship Intentions Alignment**:
   - "Slink 👀" (casual) and "Husband/wifeyyy" (serious) are incompatible
   - "No pressure, let's see where things go" is flexible and compatible with either end
   - Factor this into compatibility, but don't heavily penalize mismatches

8. **Deal-breakers** - **CRITICAL**:
   - Check each person's dealbreakers against the other's profile
   - Common dealbreakers: smoking/weed use, poor communication, lack of ambition, different values
   - Any dealbreaker match should significantly impact the score

9. **LinkedIn Insights**:
   - Use LinkedIn data to infer personality traits: sports teams → athletic, internships → driven/ambitious, non-profit work → kind/compassionate
   - Match these inferred traits with what each person values in a partner
   - Look for career/ambition alignment

10. **Media Taste Compatibility**:
    - Exact matches are a strong compatibility boost
    - Similar genres/themes count as shared interests
    - Niche or obscure shows/movies both liking suggests similar taste and stronger connection

11. **Fun Fact Analysis**:
    - Unique shared experiences or backgrounds
    - Personality quirks and humor style compatibility
    - Unexpected common interests
    - Potential conversation starters that could make a great first date

Provide your analysis in JSON format:
{{
    "compatibility_score": <number 0-100>,
    "reasoning": "<2-3 sentence explanation>",
    "shared_interests": ["<interest1>", "<interest2>"],
    "key_matches": ["<what makes them compatible>"],
    "potential_concerns": ["<any concerns>"]
}}

**IMPORTANT - Score Calibration**: Use the FULL 0-100 range. Be critical and honest:
- 0-30: Incompatible or significant dealbreakers/mismatches
- 31-50: Poor match, major concerns outweigh positives
- 51-65: Mediocre match, some compatibility but notable gaps
- 66-75: Good match, solid compatibility with minor concerns
- 76-85: Great match, strong compatibility across most dimensions
- 86-100: Exceptional match, outstanding compatibility (RARE - reserve for truly exceptional pairs)

Most matches should fall in the 40-75 range. Don't inflate scores - be selective about giving 80+."""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )

        # Parse the JSON response
        response_text = completion.choices[0].message.content

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        result = json.loads(json_str)
        return result

    except Exception as e:
        print(f"Error evaluating compatibility: {e}")
        # Return a default low score if API call fails
        return {
            "compatibility_score": 0,
            "reasoning": f"Error: {str(e)}",
            "shared_interests": [],
            "key_matches": [],
            "potential_concerns": ["API evaluation failed"]
        }


def find_matches_with_groq(df, api_key, linkedin_email=None, linkedin_password=None):
    """
    Find optimal matches using Groq API for compatibility evaluation.
    Optionally includes LinkedIn data if credentials are provided.
    """
    client = Groq(api_key=api_key)

    # Initialize LinkedIn client if credentials provided
    linkedin_client = None
    if linkedin_email and linkedin_password:
        try:
            print("Authenticating with LinkedIn...")
            linkedin_client = Linkedin(linkedin_email, linkedin_password)
            print("✓ LinkedIn authentication successful\n")
        except Exception as e:
            print(f"✗ LinkedIn authentication failed: {e}")
            print("Continuing without LinkedIn data...\n")

    n = len(df)

    # Fetch LinkedIn data for all people first
    if linkedin_client:
        print(f"Fetching LinkedIn data for {n} people...")
        for i in range(n):
            person = df.iloc[i]
            linkedin_url = person.get('linkedin_url')
            if linkedin_url and not pd.isna(linkedin_url):
                linkedin_data = get_linkedin_data(linkedin_client, linkedin_url)
                df.at[i, 'linkedin_data'] = linkedin_data
        print("✓ LinkedIn data fetching complete\n")

    compatibility = {}

    print(f"Evaluating compatibility for {n} people using Groq AI...")
    print("This may take a few minutes...\n")

    # Evaluate all compatible pairs
    pair_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            person1 = df.iloc[i]
            person2 = df.iloc[j]

            # Quick orientation check first (no API call needed)
            if not is_compatible_orientation(person1, person2):
                continue

            pair_count += 1
            print(f"Evaluating pair {pair_count}: {person1['name']} + {person2['name']}...", end=" ")

            # Use Groq to evaluate this pair
            result = evaluate_compatibility_with_groq(person1, person2, client)
            score = result['compatibility_score']

            print(f"Score: {score}%")

            if score > 0:
                compatibility[(i, j)] = {
                    'score': score,
                    'reasoning': result['reasoning'],
                    'shared_interests': result.get('shared_interests', []),
                    'key_matches': result.get('key_matches', []),
                    'potential_concerns': result.get('potential_concerns', [])
                }

    print(f"\nFound {len(compatibility)} compatible pairs")

    # Create graph for maximum weight matching
    G = nx.Graph()

    # Add all people as nodes
    for i in range(n):
        G.add_node(i)

    # Add edges with weights
    for (i, j), data in compatibility.items():
        G.add_edge(i, j, weight=data['score'])

    # Find maximum weight matching
    matching = nx.max_weight_matching(G, maxcardinality=False)

    # Convert to readable format with full compatibility data
    matches = []
    for i, j in matching:
        person1 = df.iloc[i]
        person2 = df.iloc[j]
        comp_data = compatibility.get((min(i, j), max(i, j)), {})

        matches.append({
            'person1': person1,
            'person2': person2,
            'score': comp_data.get('score', 0),
            'reasoning': comp_data.get('reasoning', ''),
            'shared_interests': comp_data.get('shared_interests', []),
            'key_matches': comp_data.get('key_matches', []),
            'potential_concerns': comp_data.get('potential_concerns', [])
        })

    # Sort by compatibility score (highest first)
    matches.sort(key=lambda x: x['score'], reverse=True)

    return matches


def export_matches(matches, output_file='matches_api.csv'):
    """Export matches to CSV file."""
    results = []

    for match in matches:
        person1 = match['person1']
        person2 = match['person2']

        results.append({
            'Person 1 Name': person1['name'],
            'Person 1 Email': person1['email'],
            'Person 1 Phone': person1.get('phone', ''),
            'Person 2 Name': person2['name'],
            'Person 2 Email': person2['email'],
            'Person 2 Phone': person2.get('phone', ''),
            'Compatibility Score': f"{match['score']}%",
            'Shared Interests': ', '.join(match['shared_interests']),
            'Key Matches': ', '.join(match['key_matches']),
            'AI Reasoning': match['reasoning'],
            'Potential Concerns': ', '.join(match['potential_concerns']),
            'Person 1 Looking For': person1.get('looking_for', ''),
            'Person 2 Looking For': person2.get('looking_for', '')
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv(output_file, index=False)
    print(f"\nMatches exported to {output_file}")
    return results_df


def main():
    """Main function to run the Groq API matcher."""
    if len(sys.argv) < 2:
        print("Usage: python matcher_api.py <responses.csv>")
        print("\nMake sure to set your GROQ_API_KEY environment variable:")
        print("  export GROQ_API_KEY='your-api-key-here'")
        print("\nGet your FREE API key at: https://console.groq.com/keys")
        sys.exit(1)

    csv_file = sys.argv[1]

    # Get API key from environment
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        print("Error: GROQ_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export GROQ_API_KEY='your-api-key-here'")
        print("\nGet your FREE API key at: https://console.groq.com/keys")
        sys.exit(1)

    # Get LinkedIn credentials (optional)
    linkedin_email = os.environ.get('LINKEDIN_EMAIL')
    linkedin_password = os.environ.get('LINKEDIN_PASSWORD')

    print("USC Blind Date Matcher - Groq AI Version (FREE) with LinkedIn")
    print("=" * 50)

    if linkedin_email and linkedin_password:
        print("LinkedIn integration: ENABLED")
    else:
        print("LinkedIn integration: DISABLED (set LINKEDIN_EMAIL and LINKEDIN_PASSWORD to enable)")

    # Load responses
    print(f"\nLoading responses from {csv_file}...")
    df = load_responses(csv_file)
    print(f"Loaded {len(df)} responses")

    # Find matches using Groq API
    print("\nFinding optimal matches using Groq AI...")
    matches = find_matches_with_groq(df, api_key, linkedin_email, linkedin_password)

    print(f"\nFound {len(matches)} matches!")
    print(f"{len(df) - (len(matches) * 2)} people unmatched")

    # Export results
    results_df = export_matches(matches)

    # Display top matches
    print("\n" + "=" * 50)
    print("TOP MATCHES:")
    print("=" * 50)
    for i, match in enumerate(matches[:10], 1):
        print(f"\nMatch #{i}: {match['score']}%")
        print(f"  {match['person1']['name']} + {match['person2']['name']}")
        print(f"  Reasoning: {match['reasoning']}")
        if match['shared_interests']:
            print(f"  Shared interests: {', '.join(match['shared_interests'])}")


if __name__ == "__main__":
    main()
