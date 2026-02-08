from __future__ import annotations


CHAPTER_TITLES: list[str] = [
    "Beginnings",
    "The Grand Search",
    "Cave-in",
    "Rivalry",
    "Not What They Seem (Part I)",
    "Not What They Seem (Part II)",
    "A New Land",
    "Around the World",
    "Journey to the Core",
    "Retirement?",
]


def chapter_title(chapter: int) -> str:
    idx = max(1, min(len(CHAPTER_TITLES), int(chapter))) - 1
    return CHAPTER_TITLES[idx]

