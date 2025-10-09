import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Language pair configurations
LANGUAGE_PAIRS = {
    'en-ja': {
        'native': 'en',
        'learning': 'ja',
        'native_name': 'English',
        'learning_name': 'Japanese',
        'romanization': 'romaji',
    },
    # Future: add more language pairs here
}

# Main configuration
CONFIG = {
    'gemini': {
        'api_key': os.getenv('GEMINI_API_KEY'),
        'model': 'gemini-2.5-flash',
    },
    
    # Active language pair - change this to switch languages
    'language_pair': 'en-ja',
    
    'generation': {
        'stories_per_day': 10,
        'difficulty_distribution': {
            'N5': 3,
            'N4': 2,
            'N3': 2,
            'N2': 2,
            'N1': 1,
        },
        'topics': [
            '科技 Technology',
            '食べ物 Food',
            '日常生活 Daily Life',
            '旅行 Travel',
            '文化 Culture',
            'ビジネス Business',
        ],
    },
    
    'output': {
        'json_dir': './output',
        'audio_dir': './output/audio',
    }
}

def get_language_config():
    """Get the current active language pair configuration"""
    pair = CONFIG['language_pair']
    if pair not in LANGUAGE_PAIRS:
        raise ValueError(f"Unknown language pair: {pair}")
    return LANGUAGE_PAIRS[pair]

def get_native_language_name():
    """Get the full name of the native language"""
    return get_language_config()['native_name']

def get_learning_language_name():
    """Get the full name of the learning language"""
    return get_language_config()['learning_name']