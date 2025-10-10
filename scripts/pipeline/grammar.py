from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class GrammarPoint:
    name: str
    explanation: str

# N5 Grammar points for Japanese, organized into groups based on README.
# Explanations are kept concise for use in prompts.

_N5_GRAMMAR_JA: Dict[int, List[GrammarPoint]] = {
    0: [
        GrammarPoint("Particle は (wa)", "Marks the topic of the sentence. (As for ...)."),
        GrammarPoint("Particle を (o)", "Marks the direct object of a verb."),
        GrammarPoint("Particle に (ni)", "Marks location of existence, a point in time, or direction/target."),
        GrammarPoint("Particle で (de)", "Marks the location of an action or the means by which an action is done."),
        GrammarPoint("Particle の (no)", "Indicates possession or attribution, like 's."),
        GrammarPoint("Copula です (desu)", "Formal verb 'to be' (is, am, are)."),
        GrammarPoint("Verb form 〜ます (~masu)", "Formal non-past affirmative verb ending."),
        GrammarPoint("Verb form 〜ました (~mashita)", "Formal past affirmative verb ending."),
        GrammarPoint("Verb form 〜ません (~masen)", "Formal non-past negative verb ending."),
        GrammarPoint("Sentence ender か (ka)", "Turns a statement into a question."),
    ],
    1: [
        GrammarPoint("Particle が (ga)", "Marks the subject of the sentence, often for emphasis or new information."),
        GrammarPoint("Particle と (to)", "Used to connect nouns ('and'), or to indicate 'with' someone."),
        GrammarPoint("Particle も (mo)", "Means 'also' or 'too', replacing は, が, or を."),
        GrammarPoint("Particle へ (e)", "Marks the direction of movement, similar to に but emphasizing direction over arrival."),
        GrammarPoint("Particle から (kara)", "Indicates a starting point in time or place ('from')."),
        GrammarPoint("Particle まで (made)", "Indicates an endpoint or limit ('until', 'up to')."),
        GrammarPoint("Verb form 〜ている (~te iru)", "Indicates a continuous or resulting state ('-ing')."),
        GrammarPoint("Verb form 〜てください (~te kudasai)", "Used to make a polite request ('Please do...')."),
        GrammarPoint("Verb form 〜ましょう (~mashou)", "Used to make a suggestion ('Let's do...')."),
        GrammarPoint("Verb form 〜たい (~tai)", "Expresses the desire to do something ('want to do...')."),
        GrammarPoint("い-Adjectives", "Adjectives ending with い that can modify nouns directly."),
        GrammarPoint("な-Adjectives", "Adjectives that require な before a noun."),
    ],
    2: [
        GrammarPoint("Verb て-form for connecting clauses", "Links multiple verb actions in sequence."),
        GrammarPoint("Comparatives (〜より〜の方)", "Structure for comparing two things (Y is more ... than X)."),
        GrammarPoint("Counters (〜つ, 〜人, etc.)", "Suffixes used for counting different types of objects, people, etc."),
        GrammarPoint("Obligation (〜なければなりません)", "Expresses necessity or obligation ('must do...')."),
        GrammarPoint("Permission (〜てもいいです)", "Expresses permission ('you may do...')."),
        GrammarPoint("Prohibition (〜てはいけません)", "Expresses prohibition ('you must not do...')."),
        GrammarPoint("Adverbial form of adjectives", "How to turn い-adjectives (く) and な-adjectives (に) into adverbs."),
        GrammarPoint("Giving and Receiving Verbs (あげる, くれる, もらう)", "Verbs for giving and receiving, which depend on the social context."),
    ]
}

def load_grammar(lang: str, level: str, group: Optional[int] = None) -> List[GrammarPoint]:
    """
    Loads a list of grammar points for a specific language, level, and group.

    Args:
        lang: The language (e.g., 'ja').
        level: The proficiency level (e.g., 'N5').
        group: The specific grammar group to load (0, 1, 2). 
               If None, all groups for the level are loaded.

    Returns:
        A list of GrammarPoint objects.
    """
    if lang.lower() != 'ja' or level.upper() != 'N5':
        # For now, only JA N5 is supported
        return []

    if group is not None:
        return _N5_GRAMMAR_JA.get(group, [])
    
    # If group is None, return all grammar points for the level
    all_grammar = []
    for g in sorted(_N5_GRAMMAR_JA.keys()):
        all_grammar.extend(_N5_GRAMMAR_JA[g])
    return all_grammar
