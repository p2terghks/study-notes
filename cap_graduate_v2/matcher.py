"""교육과정에 등록된 이름과 OCR 문자열의 자모 유사도를 비교한다."""

import unicodedata
from difflib import SequenceMatcher
from functools import lru_cache

from rules import catalog, key


# 모든 과목에 동일하게 적용하는 최소 유사도와 1·2위 점수 차이
MIN_SIMILARITY = 0.80
MIN_MARGIN = 0.04


# 선택 전공의 과목명·별칭을 표준 과목명에 연결한다.
@lru_cache
def names(track):
    known = {alias: entry[0] for alias, entry in catalog(track).items()}
    for name in ("TLC5", "채플5"):
        known[key(name)] = name
    return known


# OCR 이름을 목록과 비교해 표준 과목명을 반환한다. 모호하면 원문을 유지한다.
def match(name, track):
    known = names(track)
    # 공백과 영문 대소문자를 통일해 등록 이름 및 별칭부터 조회한다.
    typed = key(name)
    if not typed:
        return name
    if typed in known:
        return known[typed]

    # 한글 한 음절의 일부만 다를 때에도 나머지 자모가 점수에 반영된다.
    query = unicodedata.normalize("NFKD", typed)
    scores = {}
    for alias, canonical in known.items():
        candidate = unicodedata.normalize("NFKD", alias)
        # 두 자모열에서 일치한 길이의 두 배를 두 열의 전체 길이 합으로 나눈다.
        score = SequenceMatcher(None, query, candidate, autojunk=False).ratio()
        # 같은 과목의 공식 별칭들은 하나의 후보로 합친다.
        scores[canonical] = max(scores.get(canonical, 0), score)

    ranked = sorted(scores, key=scores.get, reverse=True)
    # 가장 닮은 이름도 기준에 미달하면 OCR 원문을 검토표에 남긴다.
    if not ranked or scores[ranked[0]] < MIN_SIMILARITY:
        return name
    # 서로 다른 두 과목이 비슷하게 닮았으면 하나를 임의로 고르지 않는다.
    if len(ranked) > 1 and scores[ranked[0]] - scores[ranked[1]] < MIN_MARGIN:
        return name
    return ranked[0]
