"""
USC Blind Date Matcher
Matches students based on compatibility scores from Google Form responses.
"""

import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite
import sys
from sentence_transformers import SentenceTransformer, util

# Global model variable - will be loaded lazily on first use
_similarity_model = None


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


def get_similarity_model():
    """
    Load the sentence similarity model (lazy loading).
    Uses a lightweight model optimized for semantic similarity.
    """
    global _similarity_model
    if _similarity_model is None:
        print("Loading semantic similarity model (first time only)...")
        # Using 'all-MiniLM-L6-v2' - small, fast, and good quality
        _similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded!")
    return _similarity_model


def calculate_text_similarity(text1, text2):
    """
    Calculate semantic similarity between two texts using sentence embeddings.
    Returns a score from 0 (completely different) to 1 (identical meaning).
    """
    # Handle empty or null values
    text1 = str(text1).strip()
    text2 = str(text2).strip()

    if not text1 or not text2 or text1 == 'nan' or text2 == 'nan':
        return 0.0

    # Get the model
    model = get_similarity_model()

    # Encode both texts
    embedding1 = model.encode(text1, convert_to_tensor=True)
    embedding2 = model.encode(text2, convert_to_tensor=True)

    # Calculate cosine similarity
    similarity = util.cos_sim(embedding1, embedding2).item()

    # Clamp to [0, 1] range
    return max(0.0, min(1.0, similarity))


def is_compatible_orientation(person1, person2):
    """
    Check if two people are compatible based on gender and what genders they're interested in.
    Uses the "I'm interested in" field from the form.
    """
    gender1 = str(person1.get('gender', '')).lower().strip()
    gender2 = str(person2.get('gender', '')).lower().strip()

    # Get what each person is interested in (this is a checkbox field, so it's comma-separated)
    # Split by comma and clean up whitespace
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

    # Both must be interested in each other's gender
    return True


def check_dealbreakers(person1, person2):
    """
    Check if either person has dealbreakers that eliminate compatibility.
    Returns True if compatible, False if dealbreakers exist.
    """
    dealbreakers1 = str(person1.get('dealbreakers', '')).lower()
    dealbreakers2 = str(person2.get('dealbreakers', '')).lower()

    # Check if person1's dealbreakers eliminate person2
    if 'smoker' in dealbreakers1:
        if person2.get('weed', '').lower() == 'yes':
            return False

    if 'bad communicator' in dealbreakers1:
        # We don't have a direct "communication" question, so skip this check
        pass

    # Check if person2's dealbreakers eliminate person1
    if 'smoker' in dealbreakers2:
        if person1.get('weed', '').lower() == 'yes':
            return False

    if 'bad communicator' in dealbreakers2:
        pass

    return True


def calculate_compatibility_score(person1, person2):
    """
    Calculate compatibility score between two people (0-100).
    Higher score = better match.
    """
    score = 0

    # Social battery compatibility (15 points max)
    social1 = person1.get('social_battery', '')
    social2 = person2.get('social_battery', '')
    social_scores = {
        "I'm out every night": 4,
        "I like going out but also need my nights in": 3,
        "Homebody but down for occasional plans": 2,
        "Netflix is my best friend": 1
    }
    if social1 in social_scores and social2 in social_scores:
        social_diff = abs(social_scores[social1] - social_scores[social2])
        score += max(0, 15 - (social_diff * 5))  # Closer social levels = higher score

    # Friday night compatibility (10 points max)
    if person1.get('friday_night') == person2.get('friday_night'):
        score += 10

    # Shared hobbies (20 points max)
    hobbies1 = set(str(person1.get('hobbies', '')).split(', '))
    hobbies2 = set(str(person2.get('hobbies', '')).split(', '))
    shared_hobbies = len(hobbies1.intersection(hobbies2))

    # Weight by how important shared interests are to each person
    importance1 = person1.get('shared_interests_importance', 3)
    importance2 = person2.get('shared_interests_importance', 3)
    avg_importance = (float(importance1) + float(importance2)) / 2

    hobby_score = (shared_hobbies / 3) * 20  # Max 3 shared hobbies
    hobby_score *= (avg_importance / 5)  # Scale by importance
    score += hobby_score

    # Dream date compatibility (10 points max)
    if person1.get('dream_date') == person2.get('dream_date'):
        score += 10

    # Drinking compatibility (10 points max)
    drinking1 = person1.get('drinking', '')
    drinking2 = person2.get('drinking', '')
    drinking_scores = {
        "Go out/party regularly": 4,
        "Social drinker": 3,
        "Occasionally": 2,
        "Nah, not for me": 1
    }
    if drinking1 in drinking_scores and drinking2 in drinking_scores:
        drinking_diff = abs(drinking_scores[drinking1] - drinking_scores[drinking2])
        score += max(0, 10 - (drinking_diff * 3))

    # Weed compatibility (5 points max)
    if person1.get('weed') == person2.get('weed'):
        score += 5

    # Ambition compatibility (10 points max)
    ambition1 = str(person1.get('ambition', ''))
    ambition2 = str(person2.get('ambition', ''))
    if ambition1 == ambition2 and ambition1 != '':
        score += 10
    elif 'Balanced' in ambition1 or 'Balanced' in ambition2:
        score += 5  # Balanced can work with most people

    # Partner values alignment (5 points max)
    # Give points if they value similar things in a partner
    values1 = set(str(person1.get('partner_values', '')).split(', '))
    values2 = set(str(person2.get('partner_values', '')).split(', '))
    shared_values = len(values1.intersection(values2))
    score += (shared_values / 3) * 5  # Max 3 shared values = 5 points

    # Trait matching (15 points max)
    # Match what person1 wants with person2's traits, and vice versa
    # Map form traits to partner values
    trait_to_value_map = {
        'funny': 'sense of humor',
        'smart': 'smart/intellectual',
        'hardworking': 'ambition/has goals',
        'ambitious/driven': 'ambition/has goals',
        'adventurous': 'adventurous',
        'kind/caring': 'kind/caring',
        'life of the party': 'fun/spontaneous',
        'spontaneous': 'fun/spontaneous',
        'reliable/loyal': 'good communicator',  # Stretch but related
    }

    # Get traits (how friends describe them)
    traits1 = set(str(person1.get('self_traits', '')).lower().split(', '))
    traits2 = set(str(person2.get('self_traits', '')).lower().split(', '))

    # Get partner values (what they want)
    p1_values = set(str(person1.get('partner_values', '')).lower().split(', '))
    p2_values = set(str(person2.get('partner_values', '')).lower().split(', '))

    # Check how many of person1's desired traits person2 actually has
    p1_match_count = 0
    for trait, value in trait_to_value_map.items():
        if value in p1_values and trait in traits2:
            p1_match_count += 1

    # Check how many of person2's desired traits person1 actually has
    p2_match_count = 0
    for trait, value in trait_to_value_map.items():
        if value in p2_values and trait in traits1:
            p2_match_count += 1

    # Average the two-way match and give up to 15 points
    avg_trait_matches = (p1_match_count + p2_match_count) / 2
    score += (avg_trait_matches / 3) * 15  # Max 3 matches each way = 15 points

    # Text similarity matching (10 points max)
    # Compare what person1 describes as their "type" with person2's actual description
    # and vice versa
    try:
        # Get type descriptions
        p1_type = str(person1.get('type_description', '')).strip()
        p2_type = str(person2.get('type_description', '')).strip()

        # Build a description of each person from their traits and hobbies
        p1_description = f"Personality: {person1.get('self_traits', '')}. Hobbies: {person1.get('hobbies', '')}."
        p2_description = f"Personality: {person2.get('self_traits', '')}. Hobbies: {person2.get('hobbies', '')}."

        # Calculate how well person1's desired type matches person2
        if p1_type and p1_type != 'nan':
            similarity_1_to_2 = calculate_text_similarity(p1_type, p2_description)
        else:
            similarity_1_to_2 = 0.0

        # Calculate how well person2's desired type matches person1
        if p2_type and p2_type != 'nan':
            similarity_2_to_1 = calculate_text_similarity(p2_type, p1_description)
        else:
            similarity_2_to_1 = 0.0

        # Average the two-way similarity and award up to 10 points
        avg_text_similarity = (similarity_1_to_2 + similarity_2_to_1) / 2
        score += avg_text_similarity * 10

    except Exception as e:
        # If text similarity fails for any reason, just skip it
        print(f"Warning: Text similarity calculation failed: {e}")
        pass

    return min(100, score)  # Cap at 100


def find_matches(df):
    """
    Find optimal matches using maximum weight matching algorithm.
    Returns list of (person1, person2, score) tuples.
    """
    # Create compatibility matrix
    n = len(df)
    compatibility = {}

    print(f"Calculating compatibility for {n} people...")

    for i in range(n):
        for j in range(i + 1, n):
            person1 = df.iloc[i]
            person2 = df.iloc[j]

            # Check orientation compatibility
            if not is_compatible_orientation(person1, person2):
                continue

            # Check dealbreakers
            if not check_dealbreakers(person1, person2):
                continue

            # Calculate compatibility score
            score = calculate_compatibility_score(person1, person2)

            if score > 0:
                compatibility[(i, j)] = score

    print(f"Found {len(compatibility)} compatible pairs")

    # Create graph for matching
    G = nx.Graph()

    # Add all people as nodes
    for i in range(n):
        G.add_node(i)

    # Add edges with weights (compatibility scores)
    for (i, j), score in compatibility.items():
        G.add_edge(i, j, weight=score)

    # Find maximum weight matching
    matching = nx.max_weight_matching(G, maxcardinality=False)

    # Convert to readable format
    matches = []
    for i, j in matching:
        person1 = df.iloc[i]
        person2 = df.iloc[j]
        score = compatibility.get((min(i, j), max(i, j)), 0)
        matches.append((person1, person2, score))

    # Sort by compatibility score (highest first)
    matches.sort(key=lambda x: x[2], reverse=True)

    return matches


def export_matches(matches, output_file='matches.csv'):
    """Export matches to CSV file."""
    results = []

    for person1, person2, score in matches:
        # Find shared hobbies
        hobbies1 = set(str(person1.get('hobbies', '')).split(', '))
        hobbies2 = set(str(person2.get('hobbies', '')).split(', '))
        shared_hobbies = ', '.join(hobbies1.intersection(hobbies2))

        results.append({
            'Person 1 Name': person1['name'],
            'Person 1 Email': person1['email'],
            'Person 2 Name': person2['name'],
            'Person 2 Email': person2['email'],
            'Compatibility Score': f"{score:.1f}%",
            'Shared Hobbies': shared_hobbies if shared_hobbies else 'None',
            'Person 1 Looking For': person1.get('looking_for', ''),
            'Person 2 Looking For': person2.get('looking_for', '')
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv(output_file, index=False)
    print(f"\nMatches exported to {output_file}")
    return results_df


def main():
    """Main function to run the matcher."""
    if len(sys.argv) < 2:
        print("Usage: python matcher.py <responses.csv>")
        print("\nTo get the CSV file:")
        print("1. Go to your Google Form")
        print("2. Click 'Responses' tab")
        print("3. Click the green spreadsheet icon")
        print("4. In the spreadsheet: File > Download > CSV")
        sys.exit(1)

    csv_file = sys.argv[1]

    print("USC Blind Date Matcher")
    print("=" * 50)

    # Load responses
    print(f"\nLoading responses from {csv_file}...")
    df = load_responses(csv_file)
    print(f"Loaded {len(df)} responses")

    # Find matches
    print("\nFinding optimal matches...")
    matches = find_matches(df)

    print(f"\nFound {len(matches)} matches!")
    print(f"{len(df) - (len(matches) * 2)} people unmatched")

    # Export results
    results_df = export_matches(matches)

    # Display top matches
    print("\n" + "=" * 50)
    print("TOP MATCHES:")
    print("=" * 50)
    for i, row in results_df.head(10).iterrows():
        print(f"\nMatch #{i+1}: {row['Compatibility Score']}")
        print(f"  {row['Person 1 Name']} + {row['Person 2 Name']}")
        if row['Shared Hobbies'] != 'None':
            print(f"  Shared interests: {row['Shared Hobbies']}")


if __name__ == "__main__":
    main()
