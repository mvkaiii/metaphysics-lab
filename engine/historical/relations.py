"""Frozen Bazi structural relation tables for historical activation profile v1."""


def _pairs(values):
    return frozenset(frozenset(pair) for pair in values)


def _sets(values):
    return frozenset(frozenset(items) for items in values)


CLASH_PAIRS = _pairs((
    ("子", "午"), ("丑", "未"), ("寅", "申"),
    ("卯", "酉"), ("辰", "戌"), ("巳", "亥"),
))

COMBINATION_PAIRS = _pairs((
    ("子", "丑"), ("寅", "亥"), ("卯", "戌"),
    ("辰", "酉"), ("巳", "申"), ("午", "未"),
))

THREE_HARMONY_SETS = _sets((
    ("申", "子", "辰"), ("亥", "卯", "未"),
    ("寅", "午", "戌"), ("巳", "酉", "丑"),
))

THREE_MEETING_SETS = _sets((
    ("亥", "子", "丑"), ("寅", "卯", "辰"),
    ("巳", "午", "未"), ("申", "酉", "戌"),
))

FULL_PUNISHMENT_SETS = _sets((
    ("寅", "巳", "申"),
    ("丑", "戌", "未"),
))
PAIR_PUNISHMENTS = _pairs((("子", "卯"),))
SELF_PUNISHMENTS = frozenset(("辰", "午", "酉", "亥"))

HARM_PAIRS = _pairs((
    ("子", "未"), ("丑", "午"), ("寅", "巳"),
    ("卯", "辰"), ("申", "亥"), ("酉", "戌"),
))

BREAK_PAIRS = _pairs((
    ("子", "酉"), ("丑", "辰"), ("寅", "亥"),
    ("卯", "午"), ("巳", "申"), ("未", "戌"),
))

STEM_COMBINATION_PAIRS = _pairs((
    ("甲", "己"), ("乙", "庚"), ("丙", "辛"),
    ("丁", "壬"), ("戊", "癸"),
))
