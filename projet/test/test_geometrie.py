"""Tests de base. Lancer : `python tests/test_geometrie.py` (ou `pytest`)."""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from couverture import glouton, masques_couverture, meilleure_combinaison, meilleure_paire
from geometrie import (COUR, aire, appliquer, appliquer_polygone, dedans, dedans_boite,
                       dedans_exact, generer_points, produit, rotation_autour,
                       rotation_h, translation)
from couverture import grille_positions


def test_aire_L():
    assert aire(COUR) == 78.0
    assert aire(COUR[::-1]) == 78.0          # sens de parcours indifférent


def test_dedans_cas_limites():
    assert dedans((2, 2), COUR)               # intérieur
    assert dedans((8, 4), COUR)               # sur un côté (frontière)
    assert dedans((0, 0), COUR)               # sommet
    assert dedans((2, 4), COUR)               # même y qu'un sommet, dedans
    assert not dedans((13, 4), COUR)          # même y qu'un sommet, dehors
    assert not dedans((8, 8), COUR)           # dans le creux du L
    assert not dedans((-1, 5), COUR)


def test_dedans_boite_est_fausse_sur_le_L():
    assert dedans_boite((8, 8), COUR)         # la boîte se trompe dans le creux
    assert not dedans((8, 8), COUR)


def test_exact_et_flottant_d_accord_loin_de_la_frontiere():
    for p in generer_points(COUR, 500, 3):
        assert dedans(p, COUR) == dedans_exact(p, COUR)


def test_rotation_conserve_l_aire():
    M = rotation_autour((6.0, 5.0), 37.0)
    assert abs(aire(appliquer_polygone(M, COUR)) - 78.0) < 1e-9


def test_l_ordre_des_transformations_compte():
    t, r = translation(3, 1), rotation_h(90)
    d_abord_t = appliquer(produit(r, t), (1, 0))   # translation puis rotation
    d_abord_r = appliquer(produit(t, r), (1, 0))   # rotation puis translation
    assert math.isclose(d_abord_t[0], -1, abs_tol=1e-12) and math.isclose(d_abord_t[1], 4, abs_tol=1e-12)
    assert math.isclose(d_abord_r[0], 3, abs_tol=1e-12) and math.isclose(d_abord_r[1], 2, abs_tol=1e-12)


def test_masques_et_version_naive_donnent_le_meme_resultat():
    pts = generer_points(COUR, 300, 1)
    cands = grille_positions(COUR, 5)
    paire, score = meilleure_paire(cands, pts, 3.2)
    ms = masques_couverture(cands, pts, 3.2)
    (i, j), score_m = meilleure_combinaison(ms, 2, len(pts))
    assert (cands[i], cands[j]) == paire and math.isclose(score, score_m)


def test_glouton_jamais_meilleur_que_l_exhaustif():
    pts = generer_points(COUR, 300, 2)
    ms = masques_couverture(grille_positions(COUR, 5), pts, 3.2)
    for k in (1, 2, 3):
        assert glouton(ms, k, len(pts))[1] <= meilleure_combinaison(ms, k, len(pts))[1] + 1e-12


if __name__ == "__main__":
    tests = [f for n, f in sorted(globals().items()) if n.startswith("test_")]
    for t in tests:
        t()
        print("ok  ", t.__name__)
    print(f"{len(tests)} tests réussis")
