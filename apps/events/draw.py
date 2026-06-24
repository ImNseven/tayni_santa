import random
from collections.abc import Sequence


def assign_santas[T](participant_ids: Sequence[T]) -> dict[T, T]:
    if len(participant_ids) < 2:
        raise ValueError("Need at least 2 participants")

    shuffled = list(participant_ids)
    random.shuffle(shuffled)

    n = len(shuffled)
    # кольцо: каждый дарит следующему, последний первому
    # % n замыкает цикл, поэтому никто не дарит сам себе
    return {shuffled[i]: shuffled[(i + 1) % n] for i in range(n)}
