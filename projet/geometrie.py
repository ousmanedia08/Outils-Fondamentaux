"""Géométrie du plan : polygones, appartenance, transformations homogènes.

Les fonctions `aire`, `sur_segment` et `dedans` viennent du TP6 (reprises et
corrigées). `dedans_exact` et `dedans_boite` servent de points de comparaison.
"""

from __future__ import annotations

import math
import random
from fractions import Fraction

Point = tuple[float, float]
Polygon = list[Point]
Matrice = list[list[float]]

# Plan fictif : une cour en L, parcourue dans le sens anti-horaire.
COUR: Polygon = [
    (0.0, 0.0), (12.0, 0.0), (12.0, 4.0),
    (5.0, 4.0), (5.0, 10.0), (0.0, 10.0),
]


# ---------------------------------------------------------------------------
# Mesures et appartenance
# ---------------------------------------------------------------------------
def aire(polygone: Polygon) -> float:
    """Aire par la formule du lacet (valeur absolue : sens de parcours libre)."""
    n = len(polygone)
    double_aire = sum(
        polygone[i][0] * polygone[(i + 1) % n][1]
        - polygone[(i + 1) % n][0] * polygone[i][1]
        for i in range(n)
    )
    return abs(double_aire) / 2


def boite_englobante(polygone: Polygon) -> tuple[float, float, float, float]:
    """Renvoie (xmin, xmax, ymin, ymax)."""
    xs = [p[0] for p in polygone]
    ys = [p[1] for p in polygone]
    return min(xs), max(xs), min(ys), max(ys)


def sur_segment(p: Point, a: Point, b: Point, tolerance: float = 1e-10) -> bool:
    """Indique si p est sur [a,b], extrémités comprises, à `tolerance` près.

    Le déterminant teste l'alignement, le produit scalaire teste que p est
    entre a et b. La tolérance (relative à l'échelle) absorbe les écarts
    d'arrondi des flottants ; son effet est mesuré dans l'expérience 1.
    """
    abx, aby = b[0] - a[0], b[1] - a[1]
    apx, apy = p[0] - a[0], p[1] - a[1]
    determinant = abx * apy - aby * apx
    echelle = max(1.0, abs(abx), abs(aby), abs(apx), abs(apy))
    if abs(determinant) > tolerance * echelle * echelle:
        return False
    produit = apx * abx + apy * aby
    longueur2 = abx * abx + aby * aby
    return -tolerance <= produit <= longueur2 + tolerance


def dedans(point: Point, polygone: Polygon, tolerance: float = 1e-10) -> bool:
    """Lancer de rayon ; la frontière compte comme intérieure.

    Un rayon horizontal part du point vers la droite : un nombre impair de
    croisements du contour signifie « dedans ». La convention demi-ouverte
    en y évite de compter deux fois un sommet partagé par deux côtés.
    `tolerance=0` supprime la tolérance de `sur_segment` (voir expérience 1).
    """
    x, y = point
    a_l_interieur = False
    n = len(polygone)
    for i in range(n):
        a, b = polygone[i], polygone[(i + 1) % n]
        if sur_segment(point, a, b, tolerance):
            return True
        if (a[1] > y) != (b[1] > y):
            x_croisement = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x < x_croisement:
                a_l_interieur = not a_l_interieur
    return a_l_interieur


def dedans_exact(point: Point, polygone: Polygon) -> bool:
    """Même algorithme que `dedans`, en arithmétique exacte (Fraction).

    Un float est un rationnel : `Fraction(0.1)` le représente sans erreur.
    Ici aucune tolérance : alignement et position sont décidés exactement.
    Sert de référence pour mesurer les erreurs de la version flottante.
    """
    px, py = Fraction(point[0]), Fraction(point[1])
    sommets = [(Fraction(x), Fraction(y)) for x, y in polygone]
    a_l_interieur = False
    n = len(sommets)
    for i in range(n):
        a, b = sommets[i], sommets[(i + 1) % n]
        det = (b[0] - a[0]) * (py - a[1]) - (b[1] - a[1]) * (px - a[0])
        if (det == 0 and min(a[0], b[0]) <= px <= max(a[0], b[0])
                and min(a[1], b[1]) <= py <= max(a[1], b[1])):
            return True
        if (a[1] > py) != (b[1] > py):
            x_croisement = a[0] + (py - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if px < x_croisement:
                a_l_interieur = not a_l_interieur
    return a_l_interieur


def dedans_boite(point: Point, polygone: Polygon) -> bool:
    """VERSION FAUSSE, gardée volontairement : test de la boîte englobante.

    C'est ce que j'avais écrit au TP6 (exercices 4.1, 5.1 et 6.1). Elle est
    correcte pour un rectangle et fausse pour toute forme non convexe, comme
    la cour en L. L'expérience 1 mesure l'ampleur de l'erreur.
    """
    xmin, xmax, ymin, ymax = boite_englobante(polygone)
    return xmin <= point[0] <= xmax and ymin <= point[1] <= ymax


def generer_points(polygone: Polygon, nombre: int, graine: int) -> list[Point]:
    """Points uniformes dans le polygone, par rejet dans la boîte englobante."""
    xmin, xmax, ymin, ymax = boite_englobante(polygone)
    rng = random.Random(graine)
    resultat: list[Point] = []
    while len(resultat) < nombre:
        p = (rng.uniform(xmin, xmax), rng.uniform(ymin, ymax))
        if dedans(p, polygone):
            resultat.append(p)
    return resultat


# ---------------------------------------------------------------------------
# Transformations en coordonnées homogènes (TP4)
# ---------------------------------------------------------------------------
def produit(A: Matrice, B: Matrice) -> Matrice:
    """Produit matriciel « à la main » (TP4, exercice 2.1)."""
    n, p, q = len(A), len(A[0]), len(B[0])
    if len(B) != p:
        raise ValueError("dimensions incompatibles")
    return [[sum(A[i][k] * B[k][j] for k in range(p)) for j in range(q)]
            for i in range(n)]


def translation(tx: float, ty: float) -> Matrice:
    return [[1.0, 0.0, tx], [0.0, 1.0, ty], [0.0, 0.0, 1.0]]


def rotation_h(angle_degres: float) -> Matrice:
    c = math.cos(math.radians(angle_degres))
    s = math.sin(math.radians(angle_degres))
    return [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]


def rotation_autour(centre: Point, angle_degres: float) -> Matrice:
    """Rotation autour d'un point : T(c) · R · T(-c).

    L'ordre compte : appliquée à un point, la matrice de droite agit en
    premier. On ramène d'abord le centre à l'origine, on tourne, on remet.
    """
    cx, cy = centre
    return produit(translation(cx, cy),
                   produit(rotation_h(angle_degres), translation(-cx, -cy)))


def appliquer(M: Matrice, point: Point) -> Point:
    x, y = point
    return (M[0][0] * x + M[0][1] * y + M[0][2],
            M[1][0] * x + M[1][1] * y + M[1][2])


def appliquer_polygone(M: Matrice, polygone: Polygon) -> Polygon:
    return [appliquer(M, p) for p in polygone]
