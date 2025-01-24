import re

def formatted_history(interactions):
    
    replace_patterns = [
        (r"[\n\r\f]", " "),
        (r"\s{2,}", " ")
    ]
    
    def clean_text(text):
        """Aplica los patrones de limpieza a un texto."""
        for pattern, replacement in replace_patterns:
            text = re.sub(pattern, replacement, text)
        return text.strip()

    formatted_list = []
    for interaction in interactions:
        if 'query' in interaction and interaction['query']:
            formatted_list.append({
                "role": "user",
                "content": clean_text(interaction['query'])
            })
        if 'full_response' in interaction and interaction['full_response']:
            formatted_list.append({
                "role": "assistant",
                "content": clean_text(interaction['full_response'])
            })

    return formatted_list