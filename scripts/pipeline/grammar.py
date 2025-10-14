from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

@dataclass
class GrammarPoint:
    """A single grammar point with all display formats"""
    
    # 完整名称（用于 prompt 和内部引用）
    name: str  # "Particle は (wa)"
    
    # 短格式（用于 UI 显示）
    short: str  # "は(wa)"
    
    # 拆分的组件（用于高级功能）
    japanese: str  # "は"
    romaji: str    # "wa"
    
    # 类型分类（用于未来的高级过滤）
    category: str  # "particle" | "verb" | "adjective" | "copula" | "expression"
    
    # 解释
    explanation: str


# ============================================================================
# N5 Grammar Points - Group 0: Core Basics (10 points)
# ============================================================================
_N5_GROUP_0: List[GrammarPoint] = [
    GrammarPoint(
        name="Particle は (wa)",
        short="は(wa)",
        japanese="は",
        romaji="wa",
        category="particle",
        explanation="Marks the topic of the sentence. (As for ...)."
    ),
    GrammarPoint(
        name="Particle を (o)",
        short="を(o)",
        japanese="を",
        romaji="o",
        category="particle",
        explanation="Marks the direct object of a verb."
    ),
    GrammarPoint(
        name="Particle に (ni)",
        short="に(ni)",
        japanese="に",
        romaji="ni",
        category="particle",
        explanation="Marks location of existence, a point in time, or direction/target."
    ),
    GrammarPoint(
        name="Particle で (de)",
        short="で(de)",
        japanese="で",
        romaji="de",
        category="particle",
        explanation="Marks the location of an action or the means by which an action is done."
    ),
    GrammarPoint(
        name="Particle の (no)",
        short="の(no)",
        japanese="の",
        romaji="no",
        category="particle",
        explanation="Indicates possession or attribution, like 's."
    ),
    GrammarPoint(
        name="Sentence ender か (ka)",
        short="か(ka)",
        japanese="か",
        romaji="ka",
        category="particle",
        explanation="Turns a statement into a question."
    ),
    GrammarPoint(
        name="Copula です (desu)",
        short="です(desu)",
        japanese="です",
        romaji="desu",
        category="copula",
        explanation="Formal verb 'to be' (is, am, are)."
    ),
    GrammarPoint(
        name="Copula でした (deshita)",
        short="でした(deshita)",
        japanese="でした",
        romaji="deshita",
        category="copula",
        explanation="Formal past tense of 'to be' (was, were)."
    ),
    GrammarPoint(
        name="Copula ではありません (dewa arimasen)",
        short="ではありません(dewa arimasen)",
        japanese="ではありません",
        romaji="dewa arimasen",
        category="copula",
        explanation="Formal negative of 'to be' ('is not', 'am not', 'are not')."
    ),
    GrammarPoint(
        name="Copula ではありませんでした (dewa arimasen deshita)",
        short="ではありませんでした(dewa arimasen deshita)",
        japanese="ではありませんでした",
        romaji="dewa arimasen deshita",
        category="copula",
        explanation="Formal past negative of 'to be' ('was not', 'were not')."
    ),
    GrammarPoint(
        name="Verb form 〜ます (~masu)",
        short="ます(masu)",
        japanese="ます",
        romaji="masu",
        category="verb",
        explanation="Formal non-past affirmative verb ending."
    ),
    GrammarPoint(
        name="Verb form 〜ました (~mashita)",
        short="ました(mashita)",
        japanese="ました",
        romaji="mashita",
        category="verb",
        explanation="Formal past affirmative verb ending."
    ),
    GrammarPoint(
        name="Verb form 〜ません (~masen)",
        short="ません(masen)",
        japanese="ません",
        romaji="masen",
        category="verb",
        explanation="Formal non-past negative verb ending."
    ),
    GrammarPoint(
        name="Verb います (imasu)",
        short="います(imasu)",
        japanese="います",
        romaji="imasu",
        category="verb",
        explanation="To exist (for animate things)."
    ),
    GrammarPoint(
        name="Verb いました (imashita)",
        short="いました(imashita)",
        japanese="いました",
        romaji="imashita",
        category="verb",
        explanation="Past tense of います, to exist (for animate things)."
    ),
    GrammarPoint(
        name="Verb いません (imasen)",
        short="いません(imasen)",
        japanese="いません",
        romaji="imasen",
        category="verb",
        explanation="Negative form of います, to not exist (for animate things)."
    ),
    GrammarPoint(
        name="Verb いませんでした (imasen deshita)",
        short="いませんでした(imasen deshita)",
        japanese="いませんでした",
        romaji="imasen deshita",
        category="verb",
        explanation="Past negative form of います, to not exist (for animate things)."
    ),
    GrammarPoint(
        name="Verb あります (arimasu)",
        short="あります(arimasu)",
        japanese="あります",
        romaji="arimasu",
        category="verb",
        explanation="To exist (for inanimate things); to have."
    ),
    GrammarPoint(
        name="Verb ありました (arimashita)",
        short="ありました(arimashita)",
        japanese="ありました",
        romaji="arimashita",
        category="verb",
        explanation="Past tense of あります, to exist (for inanimate things)."
    ),
    GrammarPoint(
        name="Verb ありません (arimasen)",
        short="ありません(arimasen)",
        japanese="ありません",
        romaji="arimasen",
        category="verb",
        explanation="Negative form of あります, to not exist (for inanimate things)."
    ),
    GrammarPoint(
        name="Verb ありませんでした (arimasen deshita)",
        short="ありませんでした(arimasen deshita)",
        japanese="ありませんでした",
        romaji="arimasen deshita",
        category="verb",
        explanation="Past negative form of あります, to not exist (for inanimate things)."
    ),
]


# ============================================================================
# N5 Grammar Points - Group 1: Expansion (12 points)
# ============================================================================
_N5_GROUP_1: List[GrammarPoint] = [
    GrammarPoint(
        name="Particle が (ga)",
        short="が(ga)",
        japanese="が",
        romaji="ga",
        category="particle",
        explanation="Marks the subject of the sentence, often for emphasis or new information."
    ),
    GrammarPoint(
        name="Particle と (to)",
        short="と(to)",
        japanese="と",
        romaji="to",
        category="particle",
        explanation="Used to connect nouns ('and'), or to indicate 'with' someone."
    ),
    GrammarPoint(
        name="Particle も (mo)",
        short="も(mo)",
        japanese="も",
        romaji="mo",
        category="particle",
        explanation="Means 'also' or 'too', replacing は, が, or を."
    ),
    GrammarPoint(
        name="Particle へ (e)",
        short="へ(e)",
        japanese="へ",
        romaji="e",
        category="particle",
        explanation="Marks the direction of movement, similar to に but emphasizing direction over arrival."
    ),
    GrammarPoint(
        name="Particle から (kara)",
        short="から(kara)",
        japanese="から",
        romaji="kara",
        category="particle",
        explanation="Indicates a starting point in time or place ('from')."
    ),
    GrammarPoint(
        name="Particle まで (made)",
        short="まで(made)",
        japanese="まで",
        romaji="made",
        category="particle",
        explanation="Indicates an endpoint or limit ('until', 'up to')."
    ),
    GrammarPoint(
        name="Verb form 〜ている (~te iru)",
        short="ている(te iru)",
        japanese="ている",
        romaji="te iru",
        category="verb",
        explanation="Indicates a continuous or resulting state ('-ing')."
    ),
    GrammarPoint(
        name="Verb form 〜てください (~te kudasai)",
        short="てください(te kudasai)",
        japanese="てください",
        romaji="te kudasai",
        category="verb",
        explanation="Used to make a polite request ('Please do...')."
    ),
    GrammarPoint(
        name="Verb form 〜ましょう (~mashou)",
        short="ましょう(mashou)",
        japanese="ましょう",
        romaji="mashou",
        category="verb",
        explanation="Used to make a suggestion ('Let's do...')."
    ),
    GrammarPoint(
        name="Verb form 〜たい (~tai)",
        short="たい(tai)",
        japanese="たい",
        romaji="tai",
        category="verb",
        explanation="Expresses the desire to do something ('want to do...')."
    ),
    GrammarPoint(
        name="い-Adjectives",
        short="い-adj",
        japanese="い形容詞",
        romaji="i-keiyoushi",
        category="adjective",
        explanation="Adjectives ending with い that can modify nouns directly."
    ),
    GrammarPoint(
        name="な-Adjectives",
        short="な-adj",
        japanese="な形容詞",
        romaji="na-keiyoushi",
        category="adjective",
        explanation="Adjectives that require な before a noun."
    ),
]


# ============================================================================
# N5 Grammar Points - Group 2: N5 Advanced (8 points)
# ============================================================================
_N5_GROUP_2: List[GrammarPoint] = [
    GrammarPoint(
        name="Verb て-form for connecting clauses",
        short="て-form",
        japanese="て形",
        romaji="te-kei",
        category="verb",
        explanation="Links multiple verb actions in sequence."
    ),
    GrammarPoint(
        name="Comparatives (〜より〜の方)",
        short="より〜の方",
        japanese="より〜の方",
        romaji="yori~no hou",
        category="expression",
        explanation="Structure for comparing two things (Y is more ... than X)."
    ),
    GrammarPoint(
        name="Counters (〜つ, 〜人, etc.)",
        short="Counters",
        japanese="助数詞",
        romaji="josuushi",
        category="expression",
        explanation="Suffixes used for counting different types of objects, people, etc."
    ),
    GrammarPoint(
        name="Obligation (〜なければなりません)",
        short="なければならない",
        japanese="なければならない",
        romaji="nakereba naranai",
        category="expression",
        explanation="Expresses necessity or obligation ('must do...')."
    ),
    GrammarPoint(
        name="Permission (〜てもいいです)",
        short="てもいい",
        japanese="てもいい",
        romaji="temo ii",
        category="expression",
        explanation="Expresses permission ('you may do...')."
    ),
    GrammarPoint(
        name="Prohibition (〜てはいけません)",
        short="てはいけない",
        japanese="てはいけない",
        romaji="tewa ikenai",
        category="expression",
        explanation="Expresses prohibition ('you must not do...')."
    ),
    GrammarPoint(
        name="Adverbial form of adjectives",
        short="Adv-adj",
        japanese="副詞形",
        romaji="fukushi-kei",
        category="adjective",
        explanation="How to turn い-adjectives (く) and な-adjectives (に) into adverbs."
    ),
    GrammarPoint(
        name="Giving and Receiving Verbs (あげる, くれる, もらう)",
        short="あげる/くれる/もらう",
        japanese="授受動詞",
        romaji="juju-doushi",
        category="verb",
        explanation="Verbs for giving and receiving, which depend on the social context."
    ),
]


# ============================================================================
# Organization and Helper Functions
# ============================================================================

# 组织成字典
_N5_GRAMMAR_JA: Dict[int, List[GrammarPoint]] = {
    0: _N5_GROUP_0,
    1: _N5_GROUP_1,
    2: _N5_GROUP_2,
}


def load_grammar(lang: str, level: str, group: Optional[int] = None) -> Tuple[List[GrammarPoint], List[GrammarPoint]]:
    """
    Loads grammar points, separating them into target and previous groups.

    Args:
        lang: The language (e.g., 'ja').
        level: The proficiency level (e.g., 'N5').
        group: The specific grammar group to load (0, 1, 2). 
               If None, all grammar is considered 'target'.

    Returns:
        A tuple containing two lists:
        - target_points: Grammar points for the specified group.
        - previous_points: Grammar points from all preceding groups.
    """
    if lang.lower() != 'ja' or level.upper() != 'N5':
        return [], []

    if group is None:
        all_grammar = []
        for g in sorted(_N5_GRAMMAR_JA.keys()):
            all_grammar.extend(_N5_GRAMMAR_JA[g])
        return all_grammar, []

    target_points = _N5_GRAMMAR_JA.get(group, [])
    previous_points = []
    if group > 0:
        for g in sorted(_N5_GRAMMAR_JA.keys()):
            if g < group:
                previous_points.extend(_N5_GRAMMAR_JA[g])
    
    return target_points, previous_points


def find_grammar_point(name: str, lang: str = 'ja', level: str = 'N5') -> Optional[GrammarPoint]:
    """
    Find a grammar point by its full name.
    
    Args:
        name: The full name of the grammar point (e.g., "Particle は (wa)")
        lang: The language
        level: The proficiency level
    
    Returns:
        The GrammarPoint object if found, None otherwise.
    """
    target_points, previous_points = load_grammar(lang, level)
    all_points = target_points + previous_points
    for point in all_points:
        if point.name == name:
            return point
    return None


def get_short_names(grammar_points: List[GrammarPoint]) -> List[str]:
    """
    Extract short names from a list of grammar points.
    
    Args:
        grammar_points: List of GrammarPoint objects
    
    Returns:
        List of short format names (e.g., ["は(wa)", "を(o)"])
    """
    return [gp.short for gp in grammar_points]


def get_grammar_by_category(lang: str = 'ja', level: str = 'N5', 
                           category: Optional[str] = None) -> List[GrammarPoint]:
    """
    Get grammar points filtered by category.
    
    Args:
        lang: The language
        level: The proficiency level
        category: Filter by category ('particle', 'verb', 'adjective', 'copula', 'expression')
                 If None, returns all grammar points.
    
    Returns:
        List of GrammarPoint objects
    """
    target_points, previous_points = load_grammar(lang, level)
    all_points = target_points + previous_points
    if category is None:
        return all_points
    return [gp for gp in all_points if gp.category == category]