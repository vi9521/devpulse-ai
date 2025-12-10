"""
DevPulse Topic Extractor
Extracts key topics, keywords, and phrases from developer text.

Techniques used:
- TF-IDF for keyword scoring
- N-gram extraction
- RAKE-inspired keyword ranking
- Basic entity detection (technologies, frameworks)
"""

import re
import string
from typing import List, Dict
from collections import Counter
import numpy as np

class TopicExtractor:
    """
    Extracts dominant topics and keywords from developer conversations,
    GitHub issues, and StackOverflow posts.
    """

    def __init__(self):
        self.stopwords = set([
            "the", "a", "an", "is", "are", "to", "of", "in", "for", "and", "it",
            "this", "that", "on", "with", "as", "be", "or", "by", "from", "at",
            "have", "has", "was", "were", "but", "if", "not", "your", "you"
        ])

        # Common developer tech keywords (expandable)
        self.known_technologies = [
            "react", "vue", "angular", "svelte",
            "python", "django", "flask", "fastapi",
            "nextjs", "typescript", "javascript", "node",
            "rust", "go", "java", "spring", "mongodb",
            "docker", "kubernetes", "aws", "azure", "gcp",
        ]

        print("✅ TopicExtractor initialized")

    def clean_text(self, text: str) -> List[str]:
        """Convert text into cleaned tokens."""
        text = text.lower()
        text = re.sub(r"http\S+|www.\S+", "", text)
        text = re.sub(r"`[^`]*`", "", text)  # remove inline code
        text = text.translate(str.maketrans("", "", string.punctuation))
        tokens = text.split()

        tokens = [t for t in tokens if t not in self.stopwords and len(t) > 2]
        return tokens

    def extract_ngrams(self, tokens: List[str], n: int = 2) -> List[str]:
        """Extract n-gram phrases."""
        return [" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

    def score_keywords(self, tokens: List[str]) -> Dict[str, float]:
        """Apply TF-IDF-like scoring to extract top keywords."""
        frequency = Counter(tokens)

        # Simple scoring: freq * log(len(tokens))
        total = len(tokens)
        scores = {
            word: (freq * np.log(total + 1))
            for word, freq in frequency.items()
        }

        return scores

    def detect_technologies(self, tokens: List[str]) -> List[str]:
        """Detect known technologies/frameworks from token list."""
        techs = [t for t in tokens if t in self.known_technologies]
        return list(set(techs))

    def extract_topics(self, text_list: List[str], top_n: int = 10) -> Dict:
        """
        Extract topics from multiple text samples.

        Args:
            text_list: list of issue descriptions, questions, comments
            top_n: number of top topics to return

        Returns:
            Dictionary with keywords, n-grams, and technologies
        """
        all_tokens = []

        for text in text_list:
            if not text:
                continue
            tokens = self.clean_text(text)
            all_tokens.extend(tokens)

        if not all_tokens:
            return {
                "keywords": [],
                "top_phrases": [],
                "technologies": []
            }

        # Score keywords
        keyword_scores = self.score_keywords(all_tokens)
        sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
        keywords = [k for k, _ in sorted_keywords[:top_n]]

        # Extract bi-grams and tri-grams
        bigrams = self.extract_ngrams(all_tokens, 2)
        trigrams = self.extract_ngrams(all_tokens, 3)

        # Score phrases by frequency
        phrase_counts = Counter(bigrams + trigrams)
        top_phrases = [p for p, _ in phrase_counts.most_common(top_n)]

        # Detect tech names
        technologies = self.detect_technologies(all_tokens)

        return {
            "keywords": keywords,
            "top_phrases": top_phrases,
            "technologies": technologies
        }


# Test the topic extractor
if __name__ == "__main__":
    extractor = TopicExtractor()

    sample_texts = [
        "React hooks are amazing but useEffect causes confusion.",
        "How to fix Python import errors in Django?",
        "Rust ownership model is difficult but powerful.",
        "Docker container failing to start on AWS EC2 instance."
    ]

    topics = extractor.extract_topics(sample_texts)
    print("\n=== Topics Extracted ===")
    print(topics)
