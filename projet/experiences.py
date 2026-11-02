"""Six expériences autour du placement de bornes Wi-Fi.

Chaque expérience pose une question, mesure, et écrit une conclusion dans
resultats/resultats.txt (+ une figure). Lancer : python experiences.py [--rapide]
"""

from __future__ import annotations

import argparse
import math
import random
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from couverture import (glouton, grille_positions, incertitude_95, masques_couverture,
                        meilleure_combinaison, meilleure_paire, proportion_couverte, raffiner)
from geometrie import (COUR, aire, appliquer_polygone, boite_englobante, dedans, dedans_boite,
                       dedans_exact, generer_points, rotation_autour)

SORTIE = Path(__file__).parent / "resultats"
PORTEE = 3.2
RAPPORT: list[str] = []


def ecrire(texte: str = "") -> None:
    print(texte)
    RAPPORT.append(texte)


def pente_loglog(xs, ys) -> float:
    """Pente de la droite des moindres carrés de log(y) en fonction de log(x)."""
    lx, ly = [math.log(x) for x in xs], [math.log(y) for y in ys]
    mx, my = sum(lx) / len(lx), sum(ly) / len(ly)
    return sum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sum((a - mx) ** 2 for a in lx)


# ---------------------------------------------------------------------------
# Exp. 1 : le test « dedans » est-il fiable ?
# ---------------------------------------------------------------------------
def exp1_fiabilite_dedans(rapide: bool) -> None:
    ecrire("=== Exp. 1 : fiabilité du test d'appartenance ===")
    n = 4000 if rapide else 20000
    xmin, xmax, ymin, ymax = boite_englobante(COUR)
    rng = random.Random(0)
    pts = [(rng.uniform(xmin, xmax), rng.uniform(ymin, ymax)) for _ in range(n)]
    surface_boite = (xmax - xmin) * (ymax - ymin)
    for nom, f in (("boîte englobante (TP6, fausse)", dedans_boite), ("lancer de rayon", dedans)):
        est = surface_boite * sum(f(p, COUR) for p in pts) / n
        ecrire(f"  aire estimée par Monte-Carlo, {nom:<32}: {est:7.2f}   (exacte : {aire(COUR):.2f})")

    # Flottant contre exact près de la frontière, sur la cour tournée de 30°
    # (sommets irrationnels : les arrondis jouent vraiment).
    tournee = appliquer_polygone(rotation_autour((6.0, 5.0), 30.0), COUR)
    rng = random.Random(1)
    ecrire("  désaccords avec la référence exacte, pour des points à distance d de la frontière")
    ecrire("  (cour tournée de 30° : sommets irrationnels, donc vrais arrondis ; la moitié des points est dehors) :")
    ecrire("     d      tolérance 1e-10    tolérance 0")
    total = 600 if rapide else 3000
    for d in (1e-6, 1e-9, 1e-10, 1e-11, 1e-12, 1e-14, 1e-15):
        des_tol = des_zero = 0
        for _ in range(total):
            i = rng.randrange(len(tournee))
            a, b = tournee[i], tournee[(i + 1) % len(tournee)]
            t = rng.random()
            nx, ny = b[1] - a[1], a[0] - b[0]          # normale sortante (sens anti-horaire)
            norme = math.hypot(nx, ny)
            signe = rng.choice((-1, 1))
            p = (a[0] + t * (b[0] - a[0]) + signe * d * nx / norme,
                 a[1] + t * (b[1] - a[1]) + signe * d * ny / norme)
            ref = dedans_exact(p, tournee)
            des_tol += dedans(p, tournee) != ref
            des_zero += dedans(p, tournee, tolerance=0.0) != ref
        ecrire(f"    {d:.0e}      {des_tol:5d}/{total}        {des_zero:5d}/{total}")
    ecrire("  Lecture : jusqu'à d = 1e-9 la version flottante est sans faute. Sous 1e-10, la tolérance")
    ecrire("  déclare « dedans » des points dehors (environ la moitié de l'échantillon : c'est le prix de la")
    ecrire("  tolérance, choisi volontairement). Sans tolérance, les erreurs ne viennent que des arrondis et")
    ecrire("  n'apparaissent qu'aux distances de l'ordre de l'unité d'arrondi des coordonnées (~1e-15 ici).")
    ecrire(f"  Impact sur la couverture : la bande ambiguë a une aire ~ périmètre × 1e-10 = {44 * 1e-10:.0e},")
    ecrire(f"  soit une chance sur {78 / (44 * 1e-10):.0e} qu'un point tiré y tombe : négligeable.")
    ecrire()


# ---------------------------------------------------------------------------
# Exp. 2 : vitesse de convergence de Monte-Carlo, et l'intervalle à 95 % tient-il ?
# ---------------------------------------------------------------------------
def exp2_convergence(rapide: bool) -> None:
    ecrire("=== Exp. 2 : convergence de Monte-Carlo et intervalle de confiance ===")
    tailles = [100, 300, 1000, 3000, 10000]
    reps = 25 if rapide else 80
    xmin, xmax, ymin, ymax = boite_englobante(COUR)
    surface_boite = (xmax - xmin) * (ymax - ymin)
    p_vrai = aire(COUR) / surface_boite                 # proportion exacte : 78/120
    rng = random.Random(2)
    flux = []
    for _ in range(reps):
        flux.append([dedans((rng.uniform(xmin, xmax), rng.uniform(ymin, ymax)), COUR)
                     for _ in range(tailles[-1])])
    rms, couverture = [], []
    ecrire(f"  proportion vraie (aire/boîte) = {p_vrai:.4f} ; {reps} répétitions par taille")
    ecrire("     n     erreur RMS    couverture de l'IC 95 %")
    for n in tailles:
        erreurs2, dans_ic = 0.0, 0
        for f in flux:
            p_est = sum(f[:n]) / n
            erreurs2 += (p_est - p_vrai) ** 2
            dans_ic += abs(p_est - p_vrai) <= incertitude_95(p_est, n)
        rms.append(math.sqrt(erreurs2 / reps))
        couverture.append(dans_ic / reps)
        ecrire(f"  {n:6d}    {rms[-1]:.5f}      {100 * couverture[-1]:5.1f} %")
    pente = pente_loglog(tailles, rms)
    moyenne_ic = 100 * sum(couverture) / len(couverture)
    ecrire(f"  pente de log(erreur) en fonction de log(n) : {pente:.2f}   (théorie : -0.50)")
    ecrire(f"  couverture moyenne de l'intervalle : {moyenne_ic:.1f} % (visé : 95 %, avec {reps} répétitions")
    ecrire(f"  chaque pourcentage n'est précis qu'à ±{100 * 1.96 * math.sqrt(0.95 * 0.05 / reps):.0f} points environ)")
    ecrire("  Lecture : diviser l'erreur par 10 coûte 100 fois plus de points.")
    ecrire()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.loglog(tailles, rms, "o-", label="erreur mesurée")
    ax.loglog(tailles, [rms[0] * math.sqrt(tailles[0] / n) for n in tailles], "--", label="pente −1/2")
    ax.set_xlabel("nombre de points n"); ax.set_ylabel("erreur RMS sur la proportion")
    ax.set_title("Exp. 2 : convergence de Monte-Carlo"); ax.legend(); ax.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(SORTIE / "exp2_convergence.png", dpi=140); plt.close(fig)


# ---------------------------------------------------------------------------
# Exp. 3 : coût de la recherche, naïf contre masques de bits
# ---------------------------------------------------------------------------
def exp3_cout(rapide: bool) -> None:
    ecrire("=== Exp. 3 : coût de la recherche exhaustive (k = 2) ===")
    pts = generer_points(COUR, 1800, 42)
    grilles_naif = (4, 6, 8) if rapide else (4, 6, 8, 10, 12)
    grilles_bits = (4, 6, 8, 12, 20, 28) if rapide else (4, 6, 8, 12, 20, 28, 40, 56)
    t_naif, c_naif, t_cons, t_rech, c_bits = [], [], [], [], []
    ecrire("  grille  candidats   paires   naïf (s)   masques : construction (s)   recherche des paires (s)   identique")
    for g in sorted(set(grilles_naif) | set(grilles_bits)):
        cands = grille_positions(COUR, g)
        paires = len(cands) * (len(cands) - 1) // 2
        tn = float("nan"); paire = sc = None
        if g in grilles_naif:
            d = time.perf_counter(); paire, sc = meilleure_paire(cands, pts, PORTEE)
            tn = time.perf_counter() - d; t_naif.append(tn); c_naif.append(len(cands))
        d = time.perf_counter(); ms = masques_couverture(cands, pts, PORTEE); tc = time.perf_counter() - d
        d = time.perf_counter(); (i, j), sc_b = meilleure_combinaison(ms, 2, len(pts)); tr = time.perf_counter() - d
        t_cons.append(tc); t_rech.append(tr); c_bits.append(len(cands))
        meme = "-" if paire is None else ("oui" if (cands[i], cands[j]) == paire and math.isclose(sc, sc_b) else "NON")
        ecrire(f"  {g:5d}  {len(cands):9d}  {paires:7d}  {tn:8.3f}   {tc:20.3f}   {tr:24.3f}      {meme}")
    a_naif = pente_loglog(c_naif[1:], t_naif[1:])
    a_cons = pente_loglog(c_bits[-4:], t_cons[-4:])
    a_rech = pente_loglog(c_bits[-4:], t_rech[-4:])
    ecrire(f"  exposants mesurés (temps ~ C^α, sur les plus grandes grilles de chaque méthode) :")
    ecrire(f"    naïf : α = {a_naif:.2f} ; masques, construction : α = {a_cons:.2f} ; masques, recherche : α = {a_rech:.2f}")
    k = grilles_naif[-1]
    ecrire(f"  accélération de la recherche à la grille {k} (construction comprise) : ×{t_naif[-1] / (t_cons[c_bits.index(c_naif[-1])] + t_rech[c_bits.index(c_naif[-1])]):.0f}")
    ecrire("  Lecture : le nombre de paires croît comme C² ; la version naïve refait N distances à chaque paire,")
    ecrire("  les masques les calculent une seule fois (coût linéaire en C), puis une paire ne coûte")
    ecrire("  qu'un OU binaire et un comptage de bits. Le mur quadratique reste, il est simplement repoussé.")
    ecrire()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.loglog(c_naif, t_naif, "o-", label="naïf")
    ax.loglog(c_bits, [a + b for a, b in zip(t_cons, t_rech)], "s-", label="masques (total)")
    ax.loglog(c_bits, t_rech, "^--", label="masques (recherche seule)")
    ax.set_xlabel("positions candidates C"); ax.set_ylabel("temps (s)")
    ax.set_title("Exp. 3 : coût de la recherche"); ax.legend(); ax.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(SORTIE / "exp3_cout.png", dpi=140); plt.close(fig)


# ---------------------------------------------------------------------------
# Exp. 4 : biais d'optimisme du « meilleur de beaucoup »
# ---------------------------------------------------------------------------
def exp4_biais(rapide: bool) -> None:
    ecrire("=== Exp. 4 : le meilleur score observé est-il trop beau ? ===")
    reference = generer_points(COUR, 6000 if rapide else 20000, 999)
    graines = 10 if rapide else 30
    tailles = (100, 300, 1000, 3000)
    grilles = (4, 8, 14)
    ecrire("  biais = score sur l'échantillon de recherche − score réel (échantillon de référence), en points de %")
    ecrire("  N points \\ grille  " + "".join(f"{g:>8d}" for g in grilles))
    resultats = {}
    for n in tailles:
        ligne = []
        for g in grilles:
            cands = grille_positions(COUR, g)
            somme = 0.0
            for s in range(graines):
                pts = generer_points(COUR, n, 5000 + s)
                ms = masques_couverture(cands, pts, PORTEE)
                (i, j), sc_train = meilleure_combinaison(ms, 2, n)
                somme += sc_train - proportion_couverte(reference, (cands[i], cands[j]), PORTEE)
            ligne.append(100 * somme / graines)
        resultats[n] = ligne
        ecrire(f"  {n:>8d}          " + "".join(f"{v:8.2f}" for v in ligne))
    positif = all(v > 0 for l in resultats.values() for v in l)
    ecrire(f"  Lecture : biais positif dans toutes les cases : {'oui' if positif else 'non'}. Il décroît quand l'échantillon grossit ;")
    ecrire("  l'effet du nombre de candidats n'est net que pour les petits échantillons (cases du haut).")
    ecrire("  D'où l'évaluation finale sur des points neufs, jamais utilisés pour choisir.")
    ecrire()
    fig, ax = plt.subplots(figsize=(6, 4))
    for k, g in enumerate(grilles):
        ax.semilogx(tailles, [resultats[n][k] for n in tailles], "o-", label=f"grille {g}")
    ax.set_xlabel("points d'entraînement N"); ax.set_ylabel("biais (points de %)")
    ax.set_title("Exp. 4 : biais d'optimisme"); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(SORTIE / "exp4_biais.png", dpi=140); plt.close(fig)


# ---------------------------------------------------------------------------
# Exp. 5 : glouton contre exhaustif, combien de bornes faut-il ?
# ---------------------------------------------------------------------------
def exp5_glouton(rapide: bool) -> None:
    ecrire("=== Exp. 5 : glouton contre exhaustif, nombre de bornes ===")
    n = 1500
    grille = 6 if rapide else 8
    kmax = 3 if rapide else 4
    pts = generer_points(COUR, n, 7)
    cands = grille_positions(COUR, grille)
    ms = masques_couverture(cands, pts, PORTEE)
    ecrire(f"  grille {grille} ({len(cands)} candidats), {n} points, portée {PORTEE}")
    ecrire("   k   exhaustif   glouton   rapport    t exhaustif (s)")
    exh, glo = [], []
    for k in range(1, kmax + 1):
        d = time.perf_counter(); _, se = meilleure_combinaison(ms, k, n); t = time.perf_counter() - d
        _, sg = glouton(ms, k, n)
        exh.append(se); glo.append(sg)
        ecrire(f"  {k:2d}    {100 * se:6.1f} %   {100 * sg:6.1f} %   {sg / se:6.3f}    {t:8.3f}")
    ecrire(f"  borne théorique du glouton : rapport >= 1 - 1/e = {1 - 1 / math.e:.3f}")
    cands_fin = grille_positions(COUR, 14)
    ms_fin = masques_couverture(cands_fin, pts, PORTEE)
    gains, prec = [], 0.0
    for k in range(1, 9):
        s = glouton(ms_fin, k, n)[1]
        gains.append(100 * (s - prec)); prec = s
    ecrire("  gain marginal de la k-ième borne (glouton, grille 14), en points de % :")
    ecrire("    " + "  ".join(f"k={k}: +{g:.1f}" for k, g in enumerate(gains, 1)))
    for cible in (0.90, 0.95, 0.99):
        k = next((k for k in range(1, 15) if glouton(ms_fin, k, n)[1] >= cible), None)
        ecrire(f"    couverture >= {100 * cible:.0f} % : {k if k else 'plus de 14'} bornes")
    # Le glouton est-il parfois battu ? 40 échantillons différents, k = 3.
    pires, battus = 1.0, 0
    for s in range(40):
        p = generer_points(COUR, 400, 100 + s)
        m = masques_couverture(cands, p, PORTEE)
        r = glouton(m, 3, len(p))[1] / meilleure_combinaison(m, 3, len(p))[1]
        battus += r < 1 - 1e-12
        pires = min(pires, r)
    ecrire(f"  sur 40 échantillons de 400 points (k = 3) : glouton strictement battu {battus} fois ; pire rapport {pires:.3f}")
    ecrire(f"  Lecture : le glouton est souvent battu ({battus}/40) mais de peu (pire cas {pires:.3f}) : la garantie")
    ecrire(f"  théorique ({1 - 1 / math.e:.3f}) est très pessimiste ici. Les gains marginaux décroissent avec une rupture nette :")
    ecrire(f"  les 3 premières bornes apportent {sum(gains[:3]):.0f} % de couverture, les suivantes quelques dixièmes (derniers recoins).")
    ecrire("  Pour cette cour et cette portée : 3 bornes donnent environ 90 à 94 % ; il en faut 4 pour dépasser 95 %.")
    ecrire()
    fig, ax = plt.subplots(figsize=(6, 4))
    ks = list(range(1, kmax + 1))
    ax.plot(ks, [100 * v for v in exh], "o-", label="exhaustif")
    ax.plot(ks, [100 * v for v in glo], "s--", label="glouton")
    ax.set_xlabel("nombre de bornes k"); ax.set_ylabel("couverture (%)"); ax.set_xticks(ks)
    ax.set_title("Exp. 5 : rendements décroissants"); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(SORTIE / "exp5_glouton.png", dpi=140); plt.close(fig)


# ---------------------------------------------------------------------------
# Exp. 6 : test d'invariance par rotation de la cour (matrices homogènes)
# ---------------------------------------------------------------------------
def exp6_invariance(rapide: bool) -> None:
    ecrire("=== Exp. 6 : le résultat dépend-il de l'orientation du plan ? ===")
    angles = (0, 30, 60, 90) if rapide else (0, 15, 30, 45, 60, 75, 90)
    centre = (6.0, 5.0)
    n_train, n_val = 2500, 20000 if rapide else 40000
    # Les points sont tirés UNE fois puis tournés avec la cour : les distances sont
    # conservées, donc la couverture d'un placement donné est exactement invariante.
    # Seule la grille (accrochée à la boîte englobante) peut alors faire varier le résultat.
    train0 = generer_points(COUR, n_train, 11)
    val0 = generer_points(COUR, n_val, 12)
    ecrire("  (points et cour tournés ensemble : aucun bruit d'échantillonnage entre les lignes)")
    ecrire("  angle   |aire-78|   grille: entraîn. / neufs    raffiné: entraîn. / neufs")
    g_tr, r_tr, g_val, r_val = [], [], [], []
    for ang in angles:
        M = rotation_autour(centre, ang)
        poly = appliquer_polygone(M, COUR)
        train, val = appliquer_polygone(M, train0), appliquer_polygone(M, val0)
        cands = grille_positions(poly, 6)
        ms = masques_couverture(cands, train, PORTEE)
        (i, j), sc = meilleure_combinaison(ms, 2, n_train)
        depart = (cands[i], cands[j])
        final, sc_r = raffiner(depart, train, PORTEE, poly, pas=1.0, pas_min=0.02)
        g_tr.append(sc); r_tr.append(sc_r)
        g_val.append(proportion_couverte(val, depart, PORTEE)); r_val.append(proportion_couverte(val, final, PORTEE))
        ecrire(f"  {ang:4d}°   {abs(aire(poly) - aire(COUR)):7.1e}      {100 * sc:5.1f} % / {100 * g_val[-1]:5.1f} %"
               f"         {100 * sc_r:5.1f} % / {100 * r_val[-1]:5.1f} %")
    etendue = lambda v: 100 * (max(v) - min(v))
    ecrire(f"  étendue sur l'échantillon d'entraînement : grille {etendue(g_tr):.1f} points ; raffiné {etendue(r_tr):.1f} points")
    gain = 100 * sum(b - a for a, b in zip(g_tr, r_tr)) / len(angles)
    ecrire(f"  gain moyen du raffinement (entraînement) : {gain:+.1f} points")
    ecrire("  Lecture : l'aire est invariante et, par construction du protocole, la couverture d'un placement")
    ecrire("  l'est aussi. Si le score de la grille change avec l'angle, la seule cause est la grille.")
    if etendue(g_tr) > 0.5:
        ecrire(f"  C'est le cas : {etendue(g_tr):.1f} points d'écart pour un problème géométriquement identique.")
    else:
        ecrire("  Ici l'écart est faible : le test ne met pas de dépendance nette en évidence.")
    if etendue(r_tr) < 0.75 * etendue(g_tr):
        ecrire("  Le raffinement réduit nettement cette dépendance.")
    else:
        ecrire(f"  Le raffinement ({etendue(r_tr):.1f} points d'étendue) ne réduit pas nettement cette dépendance : il gagne")
        ecrire("  en moyenne en couverture mais reste bloqué dans des optima locaux qui dépendent du point de départ.")
    ecrire()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(angles, [100 * v for v in g_tr], "o-", label="grille seule")
    ax.plot(angles, [100 * v for v in r_tr], "s-", label="grille + raffinement")
    ax.set_xlabel("rotation de la cour (degrés)"); ax.set_ylabel("couverture, échantillon d'entraînement (%)")
    ax.set_title("Exp. 6 : invariance par rotation"); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(SORTIE / "exp6_rotation.png", dpi=140); plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rapide", action="store_true", help="versions allégées (environ 20 s)")
    parser.add_argument("--seulement", type=int, nargs="*", help="numéros d'expériences à lancer")
    args = parser.parse_args()
    SORTIE.mkdir(exist_ok=True)
    experiences = {1: exp1_fiabilite_dedans, 2: exp2_convergence, 3: exp3_cout,
                   4: exp4_biais, 5: exp5_glouton, 6: exp6_invariance}
    for num, f in experiences.items():
        if not args.seulement or num in args.seulement:
            d = time.perf_counter(); f(args.rapide)
            print(f"  [exp. {num} : {time.perf_counter() - d:.1f} s]\n")
    if not args.seulement:
        (SORTIE / "resultats.txt").write_text("\n".join(RAPPORT), encoding="utf-8")


if __name__ == "__main__":
    main()
