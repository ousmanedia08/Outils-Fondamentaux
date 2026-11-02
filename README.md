# Projet Outils Fondementaux

## Organisation du dépôt

```
.
├── README.md        ce fichier : vue d'ensemble du rendu
├── tp/              mes solutions aux travaux pratiques (carnets Jupyter TP2 à TP6)
└── projet/          le projet personnel (code, tests, résultats, README détaillé)
```

- **`tp/`** : mes carnets de TP tels que je les ai écrits en séance et retravaillés. 
- **`projet/`** : le projet personnel. Le détail des résultats, des limites et de la méthode est dans [`projet/README.md`](projet/README.md).

## Le projet en bref

**Titre du projet : Analyseur de plan de campus ou de quartier.**

**Question :** Une cour en L (plan fictif, 78 unités²) doit être couverte par des bornes Wi-Fi de portée 3,2. Où les placer, combien en faut-il, et à quel point peut-on se fier au résultat ?

Le projet part d'un petit programme de placement, puis étudie ses propres limites par six expériences mesurées :
fiabilité du test « point dans un polygone » (flottants contre arithmétique exacte), 
vitesse de convergence de Monte-Carlo, coût de la recherche, 
biais d'optimisme,
nombre de bornes nécessaires,
dépendance à l'orientation du plan.

Le score d'environ 68 % correspond au meilleur placement sur l'échantillon qui sert à le choisir. Le programme l'évalue aussi sur un nouvel échantillon indépendant ; ce score est généralement un peu inférieur. Le README du projet et les expériences distinguent ces deux mesures.

## Disposition

python projet.py                  # placement de 2 bornes, comparaison manuel / optimisé
python experiences.py             # les 6 expériences (environ 35 s)
python tests/test_geometrie.py    # les tests


Les résultats sont écrits dans `projet/resultats/` (plan, figures, `resultats.txt`).

## Ce qu'on doit observer

- Sur la cour en L, le placement optimisé de 2 bornes obtient environ 68 % sur l'échantillon de recherche, contre environ 60 % pour le placement manuel. L'évaluation indépendante est détaillée séparément. Deux bornes ne suffisent pas : il en faut trois à quatre.
- Mon test d'appartenance du TP6 (boîte englobante) était faux : il estime l'aire du L à 120 au lieu de 78. Le lancer de rayon corrige l'erreur.
- L'erreur de Monte-Carlo décroît en 1/√n, et la recherche par masques de bits est environ 170 fois plus rapide que la recherche naïve, pour un résultat identique.
- Le meilleur score observé sur l'échantillon de recherche est trop optimiste : d'où l'évaluation sur des points neufs.
- Une limite non résolue : le meilleur placement dépend un peu de l'orientation du plan, et le raffinement continu ne supprime pas cette dépendance.

Les chiffres exacts, leur interprétation et les limites sont dans `projet/README.md`.

## Notions du module utilisées

Flottants et comparaison à l'arithmétique exacte (TP1), matrices homogènes et rotations (TP4), géométrie du plan : aire, lancer de rayon, Monte-Carlo (TP6), et la méthode de mesure des temps des TP2 et TP3. Les détails, y compris ce qui n'est pas utilisé et pourquoi, est dans `projet/README.md`.

## Usage de l'IA

Un assistant (Claude) a aidé à relire ma première version, à proposer les expériences, à écrire une partie du code et à rédiger la documentation.
Ce qui a été vérifié, et les conclusions de l'assistant que j'ai dû corriger, sont décrits dans `projet/README.md`, section « Usage de l'IA ».
