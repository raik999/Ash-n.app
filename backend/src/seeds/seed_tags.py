from sqlalchemy import select
from sqlalchemy.orm import Session
from entities.tag import Tag

DEFAULT_TAGS: list[tuple[str, str]] = [
    ("Ilustrador", "#22A45D"),
    ("Pintor", "#4D7CFE"),
    ("Cineasta", "#F0603C"),
    ("Escritor", "#17B8C4"),
    ("Musico", "#B32FE0"),
    ("Fotografo", "#E8A317"),
    ("Bailarin", "#E0457B"),
    ("Escultor", "#8B6C42"),
    ("Disenador", "#5B4DCE"),
    ("Animador", "#0FA3A3"),
    ("Tatuador", "#C73E3E"),
    ("Actor", "#3F8AD9"),
]


def seed_tags(db: Session) -> int:
    existing_names = set(db.execute(select(Tag.name)).scalars().all())

    created = 0
    for name, color in DEFAULT_TAGS:
        if name not in existing_names:
            db.add(Tag(name=name, color=color))
            created += 1

    if created:
        db.commit()

    return created
