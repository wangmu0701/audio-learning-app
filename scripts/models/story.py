from dataclasses import dataclass, field, asdict
from typing import List, Optional

@dataclass
class Sentence:
    """Represents a single sentence in a story"""
    sentenceId: str
    learningText: str  # Text in learning language (Japanese)
    romanization: str  # Romaji for Japanese
    nativeTranslation: str  # Translation in native language (English/Chinese)
    explanation: str  # Grammar explanation in native language
    audio: dict = field(default_factory=dict)  # {"japanese": "url", "explanation": "url"}
    
    def to_dict(self):
        return asdict(self)


@dataclass
class Story:
    """Represents a complete learning story"""
    storyId: str
    date: str  # YYYY-MM-DD
    title: str
    difficulty: str  # N5, N4, N3, N2, N1
    topics: List[str]
    
    # Language configuration
    nativeLang: str = "en"  # Native language code (en, zh, etc.)
    learningLang: str = "ja"  # Learning language code (ja, ko, etc.)
    
    durationSeconds: int = 0
    audioFiles: dict = field(default_factory=dict)  # {"nativeLang": "url", "learningLang": "url"}
    sentences: List[Sentence] = field(default_factory=list)
    
    # Metadata
    sourceNews: Optional[str] = None  # Original news source
    generatedAt: Optional[str] = None  # Timestamp
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['sentences'] = [s.to_dict() for s in self.sentences]
        return result


@dataclass
class StoryIndex:
    """Represents a story entry in the index.json file"""
    storyId: str
    date: str
    title: str
    difficulty: str
    topics: List[str]
    durationSeconds: int
    sourceFile: str  # e.g., "2025-10-08.json"
    nativeLang: str = "en"
    learningLang: str = "ja"
    
    def to_dict(self):
        """Convert to the format expected by Flutter app"""
        return {
            'storyId': self.storyId,
            'date': self.date,
            'title': self.title,
            'metadata': {
                'topics': self.topics,
                'difficulty': self.difficulty,
                'totalDurationSeconds': self.durationSeconds,
                'nativeLang': self.nativeLang,
                'learningLang': self.learningLang,
            },
            'sourceFile': self.sourceFile,
        }