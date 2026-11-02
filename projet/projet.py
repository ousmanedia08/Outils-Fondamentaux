"""Placement de bornes Wi-Fi dans une cour polygonale : programme principal.

Compare un placement manuel au meilleur placement trouvé par recherche, et
l'évalue sur des points neufs. Les études détaillées sont dans experiences.py.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from couverture import (grille_positions, incertitude_95, masques_couverture,
                        meilleure_combinaison, glouton, proportion_couverte, raffiner)
from geometrie import COUR, Point, Polygon, aire, dedans, generer_points


def dessiner(polygone: Polygon, portee: float, manuel: tuple[Point, ...],
             optimise: tuple[Point, ...], chemin: Path) -> None:
    """Trace le contour, les disques de portée et les deux placements."""
    figure, axes = plt.subplots(figsize=(8, 6))
    contour = polygone + [polygone[0]]
    axes.fill([p[0] for p in contour], [p[1] for p in contour], color="#e8edf2", label="Cour")
    for borne in manuel:
        axes.add_patch(plt.Circle(borne, portee, color="#c0392b", alpha=0.16))
        axes.scatter(*borne, color="#c0392b", marker="x", s=90)
    for borne in optimise:
        axes.add_patch(plt.Circle(borne, portee, color="#2471a3", alpha=0.20))
        axes.scatter(*borne, color="#2471a3", marker="o", s=45)
    axes.plot([], [], color="#c0392b", marker="x", linestyle="", label="Référence manuelle")
    axes.plot([], [], color="#2471a3", marker="o", linestyle="", label="Placement optimisé")
    axes.set_aspect("equal", adjustable="box")
    axes.set_xlim(min(p[0] for p in polygone) - 1, max(p[0] for p in polygone) + 1)
    axes.set_ylim(min(p[1] for p in polygone) - 1, max(p[1] for p in polygone) + 1)
    axes.set_xlabel("x"); axes.set_ylabel("y")
    axes.set_title(f"Couverture Wi-Fi estimée (portée = {portee:g})")
    axes.grid(alpha=0.2); axes.legend()
    figure.tight_layout()
    figure.savefig(chemin, dpi=160)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portee", type=float, default=3.2, help="rayon de couverture")
    parser.add_argument("--grille", type=int, default=6, help="divisions de la grille candidate")
    parser.add_argument("--bornes", type=int, default=2, help="nombre de bornes à placer")
    parser.add_argument("--essais", type=int, default=5000, help="points de validation indépendants")
    parser.add_argument("--graine", type=int, default=42, help="graine aléatoire")
    parser.add_argument("--glouton", action="store_true", help="recherche gloutonne au lieu de l'exhaustive")
    parser.add_argument("--raffiner", action="store_true", help="affine ensuite les positions (hors grille)")
    args = parser.parse_args()
    if args.portee <= 0 or args.grille < 2 or args.essais < 100 or args.bornes < 1:
        parser.error("portée > 0, grille >= 2, bornes >= 1 et essais >= 100 sont requis")

    # Référence choisie à la main (valable pour 2 bornes seulement).
    manuel: tuple[Point, ...] = ((2.0, 2.0), (3.0, 8.0))
    if not all(dedans(p, COUR) for p in manuel):
        raise ValueError("Le placement manuel doit être dans la cour.")

    debut = time.perf_counter()
    candidats = grille_positions(COUR, args.grille)
    entrainement = generer_points(COUR, 1800, args.graine)
    masques = masques_couverture(candidats, entrainement, args.portee)
    chercher = glouton if args.glouton else meilleure_combinaison
    indices, score_train = chercher(masques, args.bornes, len(entrainement))
    optimise = tuple(candidats[i] for i in indices)
    if args.raffiner:
        optimise, score_train = raffiner(optimise, entrainement, args.portee, COUR)
    duree = time.perf_counter() - debut

    # Évaluation sur des points qui n'ont pas servi au choix.
    validation = generer_points(COUR, args.essais, args.graine + 1)
    score_opt = proportion_couverte(validation, optimise, args.portee)
    inc_opt = incertitude_95(score_opt, len(validation))

    print(f"Surface exacte de la cour : {aire(COUR):.2f} unités²")
    print(f"Positions candidates : {len(candidats)} ; bornes : {args.bornes} ; "
          f"méthode : {'gloutonne' if args.glouton else 'exhaustive'}{' + raffinement' if args.raffiner else ''}")
    print(f"Temps de recherche : {duree:.3f} s")
    print(f"Meilleure couverture sur l'échantillon de recherche : {100 * score_train:.1f} %")
    if args.bornes == 2:
        score_man = proportion_couverte(validation, manuel, args.portee)
        inc_man = incertitude_95(score_man, len(validation))
        print(f"Placement manuel {manuel} : {100 * score_man:.1f} % ± {100 * inc_man:.1f} points (95 %, approx.)")
    print(f"Placement optimisé {tuple((round(x, 2), round(y, 2)) for x, y in optimise)} : "
          f"{100 * score_opt:.1f} % ± {100 * inc_opt:.1f} points (95 %, approx.)")
    if args.bornes == 2:
        print(f"Gain estimé : {100 * (score_opt - score_man):+.1f} points de pourcentage")
    print("Note : l'évaluation utilise un nouvel échantillon indépendant du choix des bornes.")

    fichier = Path(__file__).parent / "resultats" / "resultat.png"
    fichier.parent.mkdir(exist_ok=True)
    dessiner(COUR, args.portee, manuel if args.bornes == 2 else (), optimise, fichier)
    print(f"Plan enregistré dans : {fichier}")


if __name__ == "__main__":
    main()
