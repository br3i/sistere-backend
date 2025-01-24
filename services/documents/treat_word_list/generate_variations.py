import itertools

def generate_variations(text):
    vowels = "aeiou"
    accents = {"a": ["a", "á"], "e": ["e", "é"], "i": ["i", "í"], "o": ["o", "ó"], "u": ["u", "ú"]}
    words = text.split()

    # Generate variations for each word
    def get_word_variations(word):
        variations = [word]  # Start with the original word
        for i, char in enumerate(word):
            if char.lower() in accents:
                current_variations = []
                for variation in variations:
                    for acc in accents[char.lower()]:
                        new_word = variation[:i] + acc + variation[i+1:]
                        current_variations.append(new_word)
                variations = current_variations
        return list(set(variations))  # Remove duplicates

    # Combine all variations for the phrase
    all_word_variations = [get_word_variations(word) for word in words]
    combinations = list(itertools.product(*all_word_variations))

    # Create all variations with proper capitalization
    result = [" ".join(phrase) for phrase in combinations]

    # Add capitalization cases
    capitalized = [variant.capitalize() for variant in result]  # First word capitalized
    fully_capitalized = [variant.upper() for variant in result]  # All words capitalized
    first_phrase_capitalized = [" ".join([word.capitalize() for word in variant.split()]) for variant in result]  # Each word capitalized

    # Combine all variations and remove duplicates
    all_variations = sorted(set(result + capitalized + fully_capitalized + first_phrase_capitalized))

    # Ensure the original text is the first option
    if text in all_variations:
        all_variations.remove(text)  # Remove the original text if it's already in the list
    return [text] + all_variations  # Prepend the original text to the list