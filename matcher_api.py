"""
USC Blind Date Matcher - Claude API Version
Uses Claude AI to intelligently match students based on comprehensive profile analysis.
"""

import pandas as pd
import anthropic
import os
import sys
import json
import networkx as nx
from typing import Dict, List, Tuple


def load_responses(csv_file):
    """Load Google Form responses from CSV file."""
    df = pd.read_csv(csv_file)

    # Rename columns to simpler names for easier access
    column_mapping = {
        'Timestamp': 'timestamp',
        'Name (first and last)': 'name',
        'Email': 'email',
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
        'Drinking': 'drinking',
        'Weed': 'weed',
        'What matters most in a partner? (Pick your top 3)': 'partner_values',
        'How important is it that they share your interests/hobbies? (Scale 1-5)': 'shared_interests_importance',
        'Describe your type (qualities, physical type, etc.)': 'type_description',
        'Career/ambition level?': 'ambition',
        'Deal-breakers?': 'dealbreakers'
    }

    df = df.rename(columns=column_mapping)
    return df


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
    if 'men' in interested1 and 'man' in gender2:
        person1_interested = True
    elif 'women' in interested1 and 'woman' in gender2:
        person1_interested = True
    elif 'other' in interested1 and ('non-binary' in gender2 or 'other' in gender2):
        person1_interested = True

    if not person1_interested:
        return False

    # Check if person2 is interested in person1's gender
    person2_interested = False
    if 'men' in interested2 and 'man' in gender1:
        person2_interested = True
    elif 'women' in interested2 and 'woman' in gender1:
        person2_interested = True
    elif 'other' in interested2 and ('non-binary' in gender1 or 'other' in gender1):
        person2_interested = True

    if not person2_interested:
        return False

    return True


def create_person_profile(person):
    """Create a readable profile string for Claude to analyze."""
    profile = f"""
Name: {person['name']}
Gender: {person.get('gender', 'N/A')}
Year: {person.get('year', 'N/A')}
Looking for: {person.get('looking_for', 'N/A')}

Personality Traits: {person.get('self_traits', 'N/A')}
Social Battery: {person.get('social_battery', 'N/A')}
Friday Nights: {person.get('friday_night', 'N/A')}
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
""".strip()
    return profile


def evaluate_compatibility_with_claude(person1, person2, client):
    """
    Use Claude API to evaluate compatibility between two people.
    Returns a compatibility score (0-100) and reasoning.
    """
    profile1 = create_person_profile(person1)
    profile2 = create_person_profile(person2)

    prompt = f"""You are an expert matchmaker analyzing compatibility between two USC students for a blind date matching program.

Here are their profiles:

PERSON A:
{profile1}

PERSON B:
{profile2}

Please analyze their compatibility across these dimensions:
1. Personality compatibility (traits, social energy, lifestyle)
2. Shared interests and hobbies
3. What each person wants vs. what the other person offers
4. Lifestyle alignment (drinking, ambition, social habits)
5. Deal-breakers (if any)

Provide your analysis in JSON format:
{{
    "compatibility_score": <number 0-100>,
    "reasoning": "<2-3 sentence explanation>",
    "shared_interests": ["<interest1>", "<interest2>"],
    "key_matches": ["<what makes them compatible>"],
    "potential_concerns": ["<any concerns>"]
}}

Be honest - some matches will be great (80-100), some okay (50-79), some poor (0-49)."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse the JSON response
        response_text = message.content[0].text

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


def find_matches_with_claude(df, api_key):
    """
    Find optimal matches using Claude API for compatibility evaluation.
    """
    client = anthropic.Anthropic(api_key=api_key)

    n = len(df)
    compatibility = {}

    print(f"Evaluating compatibility for {n} people using Claude API...")
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

            # Use Claude to evaluate this pair
            result = evaluate_compatibility_with_claude(person1, person2, client)
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
            'Person 2 Name': person2['name'],
            'Person 2 Email': person2['email'],
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
    """Main function to run the Claude API matcher."""
    if len(sys.argv) < 2:
        print("Usage: python matcher_api.py <responses.csv>")
        print("\nMake sure to set your ANTHROPIC_API_KEY environment variable:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        sys.exit(1)

    csv_file = sys.argv[1]

    # Get API key from environment
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        sys.exit(1)

    print("USC Blind Date Matcher - Claude API Version")
    print("=" * 50)

    # Load responses
    print(f"\nLoading responses from {csv_file}...")
    df = load_responses(csv_file)
    print(f"Loaded {len(df)} responses")

    # Find matches using Claude API
    print("\nFinding optimal matches using Claude AI...")
    matches = find_matches_with_claude(df, api_key)

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
