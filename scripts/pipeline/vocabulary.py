from typing import List, Dict, Optional

# ============================================================================
# N5 Vocabulary - Group 0: Core Basics
# ============================================================================
_N5_VOCABULARY_GROUP_0: List[str] = [
    # Pronouns & Demonstratives
    "私", "あなた", "彼", "彼女", "これ", "それ", "あれ", "この", "その", "あの",
    "ここ", "そこ", "あそこ", "どれ", "どの", "どこ",

    # Nouns - People & Places
    "人", "学生", "先生", "学校", "日本", "東京", "家", "部屋", "駅", "店",

    # Nouns - Things
    "本", "机", "椅子", "ペン", "車", "猫", "犬", "食べ物", "飲み物", "水",
    "ご飯", "パン", "肉", "魚", "野菜",

    # Nouns - Time & Numbers
    "今日", "明日", "昨日", "時間", "時", "分", "月", "日", "年",
    "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "百",

    # Verbs (masu-form)
    "です", "ます", "います", "あります",
    "行きます", "来ます", "帰ります", "食べます", "飲みます",
    "見ます", "聞きます", "読みます", "書きます", "買います", "撮ります",
    "します", "勉強します", "会います", "待ちます",

    # Adjectives (i-adjectives)
    "大きい", "小さい", "新しい", "古い", "いい", "悪い", "高い", "安い",
    "おいしい", "楽しい", "難しい", "易しい", "白い", "黒い", "赤い", "青い",

    # Adjectives (na-adjectives)
    "きれい", "元気", "静か", "有名", "好き", "嫌い",

    # Adverbs & Conjunctions
    "とても", "少し", "よく", "時々", "もう", "まだ", "そして", "でも",

    # Particles
    "は", "が", "を", "に", "へ", "で", "の", "と", "も", "から", "まで", "か"
]


# ============================================================================
# N5 Vocabulary - Group 1: Everyday Expansion
# ============================================================================
_N5_VOCABULARY_GROUP_1: List[str] = [
    # Nouns - Family & Social
    "家族", "父", "母", "兄", "姉", "弟", "妹", "友達",

    # Nouns - Places
    "公園", "図書館", "銀行", "病院", "映画館", "会社", "大学",

    # Nouns - Objects & Concepts
    "新聞", "雑誌", "辞書", "宿題", "仕事", "電話", "写真", "名前",
    "朝ごはん", "昼ごはん", "晩ごはん", "お茶", "牛乳", "卵",

    # Verbs (masu-form)
    "休みます", "働きます", "終わります", "起きます", "寝ます",
    "あげます", "もらいます", "教えます", "習います", "わかります",
    "貸します", "借ります", "送ります", "切ります",

    # Adjectives (i-adjectives)
    "忙しい", "暑い", "寒い", "冷たい", "温かい", "近い", "遠い",

    # Adjectives (na-adjectives)
    "便利", "不便", "親切", "ハンサム",

    # Adverbs & Expressions
    "いつも", "全然", "後で", "すぐに", "一緒に",
]


# ============================================================================
# N5 Vocabulary - Group 2: Scenario-based
# ============================================================================
_N5_VOCABULARY_GROUP_2: List[str] = [
    # Nouns - Travel & Hobbies
    "空港", "飛行機", "地図", "旅行", "お土産", "音楽", "映画", "スポーツ", "趣味",

    # Nouns - Nature & Weather
    "天気", "雨", "雪", "山", "川", "海", "花",

    # Nouns - Abstract & Other
    "問題", "質問", "答え", "意味", "お金", "時間", "パーティー",

    # Verbs (masu-form)
    "遊びます", "泳ぎます", "走ります", "使います", "作ります", "売ります",
    "入ります", "出ます", "結婚します", "散歩します",

    # Adjectives (i-adjectives)
    "若い", "明るい", "暗い", "広い", "狭い", "重い", "軽い",

    # Adjectives (na-adjectives)
    "大丈夫", "大切", "上手", "下手", "にぎやか",

    # Adverbs & Expressions
    "ゆっくり", "まっすぐ", "たぶん", "どうして",
]


# ============================================================================
# Organization and Helper Functions
# ============================================================================

_N5_VOCABULARY_JA: Dict[int, List[str]] = {
    0: _N5_VOCABULARY_GROUP_0,
    1: _N5_VOCABULARY_GROUP_1,
    2: _N5_VOCABULARY_GROUP_2,
}


def load_vocabulary(lang: str, level: str) -> List[str]:
    """
    Loads all vocabulary for a given language and level.

    Args:
        lang: The language (e.g., 'ja').
        level: The proficiency level (e.g., 'N5').

    Returns:
        A list of vocabulary words.
    """
    if lang.lower() != 'ja' or level.upper() != 'N5':
        return []

    all_vocab = []
    for g in sorted(_N5_VOCABULARY_JA.keys()):
        all_vocab.extend(_N5_VOCABULARY_JA[g])
    return all_vocab
