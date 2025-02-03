import itertools

# Mapping of vowels with their accented versions
accents = {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú"}

# Mapping of letters with valid substitutions in Spanish
substitutions = {"b": ["b", "v"], "v": ["v", "b"]}


def classify_word(word):
    """Determines if the word is acute (aguda), grave, or esdrújula."""
    word = word.lower()
    vowels = [i for i, letter in enumerate(word) if letter in accents]

    if len(vowels) < 2:
        return "acute"

    last = vowels[-1]
    penultimate = vowels[-2] if len(vowels) > 1 else None
    antepenultimate = vowels[-3] if len(vowels) > 2 else None

    if antepenultimate is not None:
        return "esdrujula"
    elif word[-1] in "aeiouns":
        return "grave"
    else:
        return "acute"


def apply_accent(word, word_type):
    """Applies an accent to the appropriate vowel based on the word type."""
    word_list = list(word)
    vowels = [i for i, letter in enumerate(word) if letter in accents]

    if not vowels:
        return word

    if word_type == "acute" and word[-1] in "aeiouns":
        index = vowels[-1]
    elif word_type == "grave" and word[-1] not in "aeiouns":
        index = vowels[-2] if len(vowels) > 1 else vowels[-1]
    elif word_type == "esdrujula":
        index = (
            vowels[-3]
            if len(vowels) > 2
            else vowels[-2] if len(vowels) > 1 else vowels[0]
        )
    else:
        return word

    word_list[index] = accents[word_list[index]]
    return "".join(word_list)


def generate_variations(word):
    """Generates valid word variations with accents and substitutions, ensuring the original word is always first."""
    original_word = word.lower()
    word_type = classify_word(original_word)

    accented_word = apply_accent(original_word, word_type)

    options = [substitutions.get(letter, [letter]) for letter in accented_word]

    variations_set = {"".join(p) for p in itertools.product(*options)}

    # Remove the original word if it appears in the variations set
    variations_set.discard(original_word)

    # Generate versions with capitalization
    capitalized_variations = {v.capitalize() for v in variations_set}
    uppercase_variations = {v.upper() for v in variations_set}

    # Create the final list ensuring the original is first
    sorted_variations = (
        [original_word]
        + sorted(variations_set)
        + sorted(capitalized_variations)
        + sorted(uppercase_variations)
    )

    return sorted_variations
