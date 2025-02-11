import itertools
import unicodedata
import re

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


def get_textual_option(text):
    """
    Procesa el texto convirtiéndolo en minúsculas, eliminando tildes y
    caracteres especiales, excepto puntos y comas.
    """
    text = text.lower()
    text = text.replace("ñ", "\001")
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    text = text.replace("\001", "ñ")

    text = re.sub(
        r"[\x00-\x1F\x7F-\x9F\u200B\u200C\u200D\u200E\u200F\uFEFF]", " ", text
    )
    text = re.sub(r"\s{2,}", " ", text).strip()

    replacements = [
        (r"[^a-z0-9áéíóúüñ%.,:=()/\- ]", ""),
        (r"\.\s*-\s*", "."),
        (r"-{2,}", "-"),
        (r"\.{2,}", "."),
        (r"\(\.\)", ""),
        (r"/{2,}", "/"),
        (r"\s{2,}", " "),
        (r";", ","),
    ]

    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)

    return text


def generate_variations(word):
    """Generates valid word variations ensuring:
    - The original word is first.
    - The processed version is always second.
    - Other variations follow.
    """
    original_word = word  # Keep original as first
    processed_word = get_textual_option(word)  # Processed version as second

    word_type = classify_word(processed_word)
    accented_word = apply_accent(processed_word, word_type)

    options = [substitutions.get(letter, [letter]) for letter in accented_word]

    variations_set = {"".join(p) for p in itertools.product(*options)}

    # Remove the processed word if it appears in variations
    variations_set.discard(processed_word)

    # Generate versions with capitalization
    capitalized_variations = {v.capitalize() for v in variations_set}
    uppercase_variations = {v.upper() for v in variations_set}

    # Create the final list ensuring correct order
    sorted_variations = (
        [original_word, processed_word]
        + sorted(variations_set)
        + sorted(capitalized_variations)
        + sorted(uppercase_variations)
    )

    return sorted_variations
