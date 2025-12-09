config_list = [
    {
        "model": "gpt-4.1-mini",          # or gpt-4.1, gpt-4.1-preview, etc.
        "api_key": "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",
    }
]

def get_llm_config():
    llm_config = {
        "config_list": config_list,
        "temperature": 0.2,
    }
    return llm_config