import itertools


def generate_variations(text):
    vowels = "aeiou"
    accents = {
        "a": ["a", "á"],
        "e": ["e", "é"],
        "i": ["i", "í"],
        "o": ["o", "ó"],
        "u": ["u", "ú"],
    }
    words = text.split()

    # Función para verificar si una palabra tiene la tilde correctamente
    def has_correct_accents(word):
        # Tildes correctas según reglas ortográficas en español
        # Las tildes solo deben aparecer si la palabra lo requiere
        accent_rules = {
            "a": ["á"],
            "e": ["é"],
            "i": ["í"],
            "o": ["ó"],
            "u": ["ú"],
            "á": ["á"],
            "é": ["é"],
            "í": ["í"],
            "ó": ["ó"],
            "ú": ["ú"],
        }

        for char in word:
            if char in accent_rules:
                # Si tiene tilde, debe ser el carácter correcto de acuerdo con las reglas
                correct_chars = accent_rules.get(char, [])
                if char not in correct_chars:
                    return False  # Si la tilde es incorrecta, la palabra es inválida
        return True

    # Generate variations for each word
    def get_word_variations(word):
        variations = [word]  # Start with the original word
        for i, char in enumerate(word):
            if char.lower() in accents:
                current_variations = []
                for variation in variations:
                    for acc in accents[char.lower()]:
                        new_word = variation[:i] + acc + variation[i + 1 :]
                        current_variations.append(new_word)
                variations = current_variations
        return list(set(variations))  # Remove duplicates

    # Combine all variations for the phrase
    all_word_variations = [get_word_variations(word) for word in words]
    combinations = list(itertools.product(*all_word_variations))

    # Crear solo variaciones que sean correctas según la regla de tildes
    valid_combinations = [
        " ".join(phrase)
        for phrase in combinations
        if has_correct_accents(" ".join(phrase))
    ]

    # Add capitalization cases
    capitalized = [
        variant.capitalize() for variant in valid_combinations
    ]  # First word capitalized
    fully_capitalized = [
        variant.upper() for variant in valid_combinations
    ]  # All words capitalized
    first_phrase_capitalized = [
        " ".join([word.capitalize() for word in variant.split()])
        for variant in valid_combinations
    ]  # Each word capitalized

    # Combine all variations and remove duplicates
    all_variations = sorted(
        set(
            valid_combinations
            + capitalized
            + fully_capitalized
            + first_phrase_capitalized
        )
    )

    # Ensure the original text is the first option
    if text in all_variations:
        all_variations.remove(
            text
        )  # Remove the original text if it's already in the list
    return [text] + all_variations  # Prepend the original text to the list
