# Où placer des bornes Wi-Fi ? Placement, précision et coût de calcul

## La question

Une cour en L (plan fictif, 78 unités²) doit être couverte par des bornes Wi-Fi de portée 3,2. **Où les placer, combien en faut-il, et à quel point peut-on se fier au résultat ?**

Le programme principal répond à la première question. Six expériences (`experiences.py`) répondent à la troisième : à chaque fois, une question, une mesure, une conclusion, y compris quand elle contredit ce que j'attendais.

##  Depuis ce dossier :

```bash
python projet.py                                   # 2 bornes, comparaison manuel / optimisé
python projet.py --bornes 3 --glouton --raffiner   # 3 bornes, recherche gloutonne puis affinage
python experiences.py                              # les 6 expériences (~35 s) -> resultats/
python experiences.py --rapide                     # version allégée (~10 s)
python tests/test_geometrie.py                     # 8 tests
```

Options de `projet.py` : `--portee`, `--grille`, `--bornes`, `--essais`, `--graine`, `--glouton`, `--raffiner`.
Les sorties sont écrites dans `resultats/` : `resultat.png` (le plan), `resultats.txt` (le texte complet des expériences) et une figure par expérience.

## Ce que les expériences ont montré

**1. Fiabilité du test d'appartenance.** *D'abord, mon `dedans` du TP6 était faux.* Au TP6, j'avais écrit `dedans` comme un test de boîte englobante. Sur la cour en L, l'aire estimée par Monte-Carlo vaut **120** au lieu de **78** : la boîte compte le creux du L. Le lancer de rayon donne 78,5 (n = 20 000). Cette version fausse est gardée dans `geometrie.py` (`dedans_boite`) pour que l'erreur reste visible et testée.

*Ensuite, flottants contre arithmétique exacte.* En comparant `dedans` à une version en `Fraction` (exacte) pour des points tombant à une distance d de la frontière, la version flottante ne se trompe jamais jusqu'à d = 1e-9. Sous 1e-10, c'est la **tolérance** de `sur_segment` qui déclare « dedans » des points dehors (environ un sur deux). Sans tolérance, il ne reste que les erreurs d'arrondi, visibles uniquement à d ≈ 1e-15 (296 désaccords sur 3 000). La bande concernée est si fine (aire ≈ 4e-9) qu'elle n'influence jamais une couverture.

**2. Précision de Monte-Carlo.** L'erreur décroît comme n^(-0,51) (théorie : n^(-1/2)) : diviser l'erreur par 10 coûte 100 fois plus de points. L'intervalle à 95 % annoncé contient la vraie valeur dans 94,5 % des cas (80 répétitions, donc ±5 points de précision sur ce chiffre) : la formule est fiable.

**3. Coût de la recherche.** La première version teste toutes les paires en recalculant les distances à chaque fois : temps ∝ C^2,08 (C = nombre de candidats), soit 5 s pour 95 candidats. Avec des masques de bits (chaque candidat → un entier dont le bit i vaut 1 si le point i est couvert), les distances ne sont calculées qu'une fois et une paire coûte un OU et un comptage de bits. Résultat identique (vérifié sur 5 tailles), **×170 plus rapide** à 95 candidats. Le mur quadratique reste (exposant 2,06 pour la recherche des paires), il est seulement repoussé : 2 000 candidats en 1,2 s.

**4. Le meilleur de beaucoup est trop beau.** Le score observé sur l'échantillon qui a servi à choisir surestime le score réel : de +6 à +9 points avec 100 points, +0,4 à +0,9 avec 3 000. D'où l'évaluation finale sur des points neufs (déjà présente dans ma première version, maintenant mesurée).

**5. Combien de bornes ?** Avec la portée 3,2, **deux bornes ne suffisent pas** : 68 % de couverture. Trois en donnent 90 à 94 %, quatre dépassent 95 %, six atteignent 99 % (glouton). Le gain d'une borne tombe de +25 points (3ᵉ) à +4 (4ᵉ) puis moins d'un point. La recherche gloutonne est battue dans 35 cas sur 40 par l'exhaustive, mais de peu (pire rapport 0,87) : la garantie théorique de 63 % est très pessimiste ici.

**6. Dépendance à l'orientation.** En tournant la cour (matrices homogènes) avec ses points, la couverture d'un placement donné est exactement la même, mais le meilleur placement trouvé sur la grille varie de **1,6 point** selon l'angle, probablement parce que la grille est accrochée à la boîte englobante (hypothèse, voir les limites). Le raffinement continu (pas divisé par 2) gagne en moyenne +2,2 points mais **ne supprime pas** cette dépendance (étendue 1,5 point) : il reste coincé dans des optima locaux. C'est une limite que je n'ai pas résolue.

## Limites

- Une portée circulaire uniforme ne décrit pas un vrai signal Wi-Fi (murs, étages, interférences ignorés).
- Un seul plan, fictif. Les conclusions chiffrées valent pour cette cour et cette portée.
- La cause de l'expérience 6 (grille liée à la boîte englobante) est une hypothèse plausible, non testée isolément.
- Le raffinement est une recherche locale sur une fonction en escalier : aucune garantie d'optimum global.
- L'exhaustif devient impraticable dès que k grandit (nombre de combinaisons) ; seul le glouton passe à l'échelle.
- Les marges d'incertitude ne couvrent que l'échantillonnage, pas les limites du modèle.

## Notions du cours mobilisées

- **TP1 (flottants)** : tolérance, arrondis, comparaison à l'arithmétique exacte (exp. 1). *Le notebook TP1 ne figurait pas dans mon dossier de travaux ; je m'appuie sur le programme du cours.*
- **TP4 (matrices)** : produit matriciel à la main, translation et rotation homogènes, rotation autour d'un point par `T(c)·R·T(-c)`, importance de l'ordre (testé).
- **TP6 (géométrie)** : aire par le lacet, lancer de rayon, déterminant, Monte-Carlo.
- **Méthode des TP2 et TP3** : mesurer le temps pour plusieurs tailles et en déduire l'exposant (exp. 3), pas divisé par 2 dans le raffinement. Je n'utilise pas l'arithmétique modulaire ni les polynômes : ils ne servent pas à cette question.

## Usage de l'IA

Un assistant (Claude) a servi à : relire ma première version, proposer les expériences, écrire une partie du code (`couverture.py`, `experiences.py`, la découpe en modules) et rédiger ce document.

Ce qui a été vérifié : les 8 tests passent ; la version à masques de bits donne le même résultat que ma version d'origine ; `projet.py` reproduit exactement les chiffres de ma première version (60,2 % et 68,2 %). Plusieurs conclusions écrites trop vite par l'assistant ont été corrigées après relecture des mesures : « rendements décroissants » (faux pour les 3 premières bornes), « le raffinement réduit la dépendance à l'angle » (faux), et un protocole de l'expérience 6 qui mélangeait l'effet cherché avec le bruit d'échantillonnage.
