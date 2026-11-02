# Amélioré un signal Wi-fi

## Pourquoi ce projet ?

Dans mon quartier au Sénégal, les bornes Wi-Fi sont souvent réajustées parce que le signal devient faible. Après quelques recherches, j'ai vu que leur position pouvait jouer un rôle. Je me suis donc demandé si je pouvais représenter ce problème avec les notions de mathématiques vues en TP.

Je ne cherche pas à expliquer toutes les raisons pour lesquelles un vrai signal baisse. Je veux surtout essayer une idée simple : est-ce que changer l'emplacement de deux bornes améliore la couverture d'une cour ? Pour donner une portée aux bornes, j'utilise aussi un petit modèle mathématique du signal et je cherche son seuil avec la dichotomie.

## Mon idée

Je dessine une cour fictive en forme de L. Le programme compare deux façons de placer deux bornes Wi-Fi. Il colore en vert les endroits où une borne est assez proche et en rouge les endroits où le Wi-Fi ne passe pas.

Le placement proposé met une borne dans chaque branche de la cour. Le programme affiche le pourcentage de points couverts pour les deux placements afin de voir lequel fonctionne mieux. C'est une comparaison sur un plan inventé, pas un conseil de réglage pour une vraie installation Wi-Fi.

## Lancer le programme

Il faut Python et Matplotlib. Dans ce dossier, lancer :

```bash
python -m pip install matplotlib
python -m pip install -r requirements.txt
python projet.py
```

Le programme affiche deux cartes côte à côte et crée aussi l'image `carte_wifi.png`.

## Comment ça marche

Le programme utilise des notions de plusieurs TP, avec des fonctions courtes et des boucles :

- la formule du lacet pour calculer l'aire de la cour ;
- le lancer de rayon pour savoir si un point est dans la cour ;
- le théorème de Pythagore pour calculer la distance entre un point et une borne ;
- un polynôme et la dichotomie pour trouver la portée associée au seuil de signal (TP3) ;
- des nombres à virgule et une tolérance pour arrêter la dichotomie (TP1) ;
- une mesure du temps pour comparer trois tailles de grille (TP2) ;
- des boucles pour parcourir le plan et compter les points couverts (TP6).

La qualité du signal est représentée par la formule inventée `100 - 8 × distance - distance²`. Ce n'est pas une formule réelle du Wi-Fi. Le seuil est fixé à 60 %. La dichotomie trouve la distance à laquelle cette formule descend jusqu'au seuil ; cette distance devient la portée utilisée pour colorier la carte.

La carte est découpée en petits points. Pour chaque point dans la cour, le programme regarde si la qualité calculée depuis au moins une borne atteint le seuil. Le cercle bleu de chaque borne est dessiné avec une boucle qui calcule ses points. Le pourcentage est une estimation basée sur cette grille : une grille plus fine donne une carte plus précise, mais demande plus de calculs.

## Changer le plan

Dans `projet.py`, les premières lignes permettent de modifier le plan, les bornes, le seuil du signal et la précision de la dichotomie. Tu peux aussi modifier la formule de `qualite_signal` et voir comment la portée calculée change.

Le temps mesuré change selon l'ordinateur. Il sert seulement à comparer les tailles de grille sur la même machine.

## Limites

Le plan et la formule du signal sont inventés. Le programme ne simule pas les murs, les étages ou les interférences d'un vrai réseau Wi-Fi. Il montre comment des notions de maths peuvent aider à comparer deux placements, pas une garantie de couverture réelle. Le projet n'utilise pas les notions de chiffrement du TP5, car elles ne servent pas à répondre à cette question.

## Usage de l'IA

L'IA (ChatGPT) a aidé à écrire les fonctions mathématiques. Elle a aussi était d'une grande aide dans la structuration du code même s'il a fallu derrière beaucoups de modification et de documentation car le code fourni était trop complexe et s'éloigner de mes objectifs.
