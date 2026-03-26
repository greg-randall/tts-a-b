import math
import random

# Elo Configuration
DEFAULT_RATING = 1000.0
K_FACTOR = 32.0
MIN_MATCHES_RELIABILITY = 10.0

def get_expected_score(rating_a, rating_b):
    """Calculate expected score for player A."""
    return 1.0 / (1.0 + pow(10, (rating_b - rating_a) / 400.0))

def calculate_updated_ratings(voice_a, voice_b, winner_name):
    """
    Update Elo ratings and stats based on a test result.
    voice_a and voice_b are Voice model instances.
    """
    # Count matches
    voice_a.matches += 1
    voice_b.matches += 1
    
    # Track wins/losses
    if winner_name == voice_a.name:
        voice_a.wins += 1
        voice_b.losses += 1
    else:
        voice_b.wins += 1
        voice_a.losses += 1
    
    # Calculate expected scores
    expected_a = get_expected_score(voice_a.rating, voice_b.rating)
    expected_b = get_expected_score(voice_b.rating, voice_a.rating)
    
    # Actual scores
    actual_a = 1.0 if winner_name == voice_a.name else 0.0
    actual_b = 1.0 if winner_name == voice_b.name else 0.0
    
    # Dynamic K-factor (more conservative with more matches)
    k_a = min(K_FACTOR, K_FACTOR / math.sqrt(max(1, voice_a.matches)))
    k_b = min(K_FACTOR, K_FACTOR / math.sqrt(max(1, voice_b.matches)))
    
    # Update ratings
    voice_a.rating += k_a * (actual_a - expected_a)
    voice_b.rating += k_b * (actual_b - expected_b)

def get_targeted_voices(voices, tested_pairs, voice_test_counts, exclude=None):
    """
    Selects a pair of voices for testing.
    Prioritizes 'anchoring' new voices by comparing them to vetted voices,
    while ensuring variety and favoring similar ratings for fine-tuning.
    exclude: set/list of voice names that appeared in the previous trial.
    """
    if len(voices) < 2:
        return []

    excluded = set(exclude) if exclude else set()
    candidate_pairs = []

    # Constants for selection logic
    VETTED_THRESHOLD = MIN_MATCHES_RELIABILITY  # 10
    NEW_THRESHOLD = 3

    # Average match count across all voices (used to penalize over-tested voices)
    avg_count = sum(voice_test_counts.values()) / len(voice_test_counts) if voice_test_counts else 0
    
    for i in range(len(voices)):
        for j in range(i + 1, len(voices)):
            voice_a = voices[i]
            voice_b = voices[j]
            pair_key = f"{voice_a.name}-{voice_b.name}"
            reverse_pair_key = f"{voice_b.name}-{voice_a.name}"
            
            # Skip if this pair has been tested
            if pair_key in tested_pairs or reverse_pair_key in tested_pairs:
                continue

            # Skip if either voice appeared in the previous trial
            if voice_a.name in excluded or voice_b.name in excluded:
                continue
                
            score = 0
            count_a = voice_test_counts.get(voice_a.name, 0)
            count_b = voice_test_counts.get(voice_b.name, 0)
            
            # 1. Base Priority: Both voices need more matches to reach 'vetted' status
            # Max 20 points
            needs_a = max(0, VETTED_THRESHOLD - count_a)
            needs_b = max(0, VETTED_THRESHOLD - count_b)
            score += (needs_a + needs_b)
            
            # 2. Anchor Bonus: Favor (New vs Vetted) to connect new voices to the network
            # This helps jump-start the global ranking for new additions.
            is_new_a = count_a < NEW_THRESHOLD
            is_new_b = count_b < NEW_THRESHOLD
            is_vetted_a = count_a >= VETTED_THRESHOLD
            is_vetted_b = count_b >= VETTED_THRESHOLD
            
            if (is_new_a and is_vetted_b) or (is_new_b and is_vetted_a):
                score += 15.0 # Significant bonus for anchoring
            elif is_new_a and is_new_b:
                score += 5.0  # Moderate bonus for new vs new, but anchor is better
            
            # 3. Similarity Score: Favor comparing voices with similar rankings
            # Only really important once they have at least one match
            if count_a > 0 or count_b > 0:
                rating_diff = abs(voice_a.rating - voice_b.rating)
                # Max 10 points for perfect match, tapering off
                similarity_score = 10.0 / (1.0 + (rating_diff / 100.0))
                score += similarity_score
            
            # 4. Match balance: penalize pairs where both voices are well above average.
            # Uses the lesser excess so one very over-tested voice doesn't unfairly
            # penalize an anchor pair with a new voice.
            excess_a = max(0, count_a - avg_count)
            excess_b = max(0, count_b - avg_count)
            score -= min(excess_a, excess_b) * 1.0
            
            candidate_pairs.append({
                'pair': (voice_a, voice_b),
                'score': score
            })
            
    if candidate_pairs:
        # Shuffle first to ensure variety among equal/similar scores
        random.shuffle(candidate_pairs)
        candidate_pairs.sort(key=lambda x: x['score'], reverse=True)
        
        # Pick from a larger pool of top candidates to ensure variety
        top_count = min(10, len(candidate_pairs))
        selected = random.choice(candidate_pairs[:top_count])
        
        # Randomize which voice is A and which is B
        selected_pair = list(selected['pair'])
        random.shuffle(selected_pair)
        return selected_pair
        
    # Fallback: Closest ranked pair if all untested pairs are exhausted
    ranked_voices = sorted(voices, key=lambda x: x.rating)
    closest_pairs = []
    for i in range(len(ranked_voices) - 1):
        if ranked_voices[i].name in excluded or ranked_voices[i+1].name in excluded:
            continue
        diff = abs(ranked_voices[i].rating - ranked_voices[i+1].rating)
        closest_pairs.append({
            'pair': (ranked_voices[i], ranked_voices[i+1]),
            'diff': diff
        })
        
    if closest_pairs:
        closest_pairs.sort(key=lambda x: x['diff'])
        top_count = min(5, len(closest_pairs))
        selected = random.choice(closest_pairs[:top_count])
        return list(selected['pair'])
        
    # Ultimate fallback
    return random.sample(voices, 2)
