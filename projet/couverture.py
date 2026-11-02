"""Placement de bornes Wi-Fi : candidats, score de couverture, recherche.

Une borne couvre les points situés à distance <= portée (disque). On cherche
k positions qui couvrent la plus grande proportion d'un échantillon de points
de la cour. Trois manières de chercher sont comparées :
  - exhaustive naïve (celle de la première version),
  - exhaustive par masques de bits (même résultat, beaucoup plus rapide),
  - gloutonne (une borne à la fois), puis raffinement continu.
"""

from __future__ import annotations

import itertools

from geometrie import Point, Polygon, boite_englobante, dedans


def grille_positions(polygone: Polygon, divisions: int) -> list[Point]:
    """Centres des cases d'une grille régulière qui tombent dans la cour."""
    xmin, xmax, ymin, ymax = boite_englobante(polygone)
    positions = []
    for i in range(divisions):
        x = xmin + (i + 0.5) * (xmax - xmin) / divisions
        for j in range(divisions):
            y = ymin + (j + 0.5) * (ymax - ymin) / divisions
            if dedans((x, y), polygone):
                positions.append((x, y))
    return positions


def est_couvert(point: Point, bornes: tuple[Point, ...], portee: float) -> bool:
    """Au moins une borne à distance <= portée (carrés : pas de racine)."""
    r2 = portee * portee
    return any((point[0] - b[0]) ** 2 + (point[1] - b[1]) ** 2 <= r2 for b in bornes)


def proportion_couverte(points: list[Point], bornes: tuple[Point, ...], portee: float) -> float:
    return sum(est_couvert(p, bornes, portee) for p in points) / len(points)


def incertitude_95(proportion: float, nombre: int) -> float:
    """Demi-largeur approchée de l'intervalle de confiance à 95 % (loi normale)."""
    return 1.96 * (proportion * (1 - proportion) / nombre) ** 0.5


# ---------------------------------------------------------------------------
# Recherche exhaustive naïve (version 1)
# ---------------------------------------------------------------------------
def meilleure_paire(candidats: list[Point], points: list[Point], portee: float
                    ) -> tuple[tuple[Point, Point], float]:
    """Teste toutes les paires ; coût ~ C² · N distances."""
    if len(candidats) < 2:
        raise ValueError("Il faut au moins deux positions candidates dans la cour.")
    meilleure, meilleur = None, -1.0
    for paire in itertools.combinations(candidats, 2):
        score = proportion_couverte(points, paire, portee)
        if score > meilleur:
            meilleure, meilleur = paire, score
    return meilleure, meilleur


# ---------------------------------------------------------------------------
# Masques de bits : chaque candidat -> entier dont le bit i vaut 1 si le point
# i est couvert. Un ensemble de bornes couvre l'union (OU bit à bit) ; le score
# est le nombre de bits à 1. Les distances ne sont calculées qu'une fois.
# ---------------------------------------------------------------------------
def masques_couverture(candidats: list[Point], points: list[Point], portee: float) -> list[int]:
    r2 = portee * portee
    masques = []
    for (bx, by) in candidats:
        m = 0
        for i, (px, py) in enumerate(points):
            if (px - bx) ** 2 + (py - by) ** 2 <= r2:
                m |= 1 << i
        masques.append(m)
    return masques


def meilleure_combinaison(masques: list[int], k: int, nombre_points: int
                          ) -> tuple[tuple[int, ...], float]:
    """Exhaustif sur toutes les combinaisons de k candidats (indices)."""
    meilleure, meilleur = None, -1
    for combo in itertools.combinations(range(len(masques)), k):
        union = 0
        for i in combo:
            union |= masques[i]
        score = union.bit_count()
        if score > meilleur:
            meilleure, meilleur = combo, score
    return meilleure, meilleur / nombre_points


def glouton(masques: list[int], k: int, nombre_points: int
            ) -> tuple[tuple[int, ...], float]:
    """À chaque tour, ajoute la borne qui couvre le plus de points nouveaux."""
    choisis: list[int] = []
    union = 0
    for _ in range(k):
        i = max(range(len(masques)), key=lambda j: (union | masques[j]).bit_count())
        choisis.append(i)
        union |= masques[i]
    return tuple(choisis), union.bit_count() / nombre_points


# ---------------------------------------------------------------------------
# Raffinement continu : recherche par coordonnées, pas divisé par 2 (esprit de
# la dichotomie, TP3). Le score est une fonction en escalier : pas de dérivée.
# ---------------------------------------------------------------------------
def raffiner(bornes: tuple[Point, ...], points: list[Point], portee: float,
             polygone: Polygon, pas: float = 1.0, pas_min: float = 0.01
             ) -> tuple[tuple[Point, ...], float]:
    """Déplace chaque borne de ±pas en x ou y tant que le score augmente.

    Quand plus aucun déplacement n'améliore, le pas est divisé par 2. Une
    borne doit rester dans la cour. S'arrête quand pas < pas_min.
    """
    courant = list(bornes)
    score = proportion_couverte(points, tuple(courant), portee)
    while pas >= pas_min:
        amelioration = True
        while amelioration:
            amelioration = False
            for i in range(len(courant)):
                for dx, dy in ((pas, 0), (-pas, 0), (0, pas), (0, -pas)):
                    essai = (courant[i][0] + dx, courant[i][1] + dy)
                    if not dedans(essai, polygone):
                        continue
                    nouveau = courant[:i] + [essai] + courant[i + 1:]
                    s = proportion_couverte(points, tuple(nouveau), portee)
                    if s > score:
                        courant, score = nouveau, s
                        amelioration = True
        pas /= 2
    return tuple(courant), score
