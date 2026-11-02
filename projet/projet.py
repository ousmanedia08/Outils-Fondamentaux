"""Carte très simple pour comparer deux placements de bornes Wi-Fi."""

import math
import time
import matplotlib.pyplot as plt


# Le plan est inventé. Chaque paire donne les coordonnées d'un coin de la cour.
cour = [(0, 0), (12, 0), (12, 4), (5, 4), (5, 10), (0, 10)]

# Chaque borne est un point (x, y).
# Le premier placement met les deux bornes du côté gauche de la cour.
placement_depart = [(2, 2), (3, 8)]

# Dans le placement proposé, une borne est dans chaque branche de la cour en L.
placement_propose = [(2.5, 7.5), (9, 2)]

seuil_signal = 60
tolerance = 0.01  # précision demandée pour la recherche de la portée
pas = 0.2  # distance entre les points utilisés pour colorier la carte


def qualite_signal(eloignement):
    """Petit modèle inventé : la qualité baisse quand on s'éloigne."""
    return 100 - 8 * eloignement - eloignement * eloignement


def chercher_portee(seuil):
    """Utilise la dichotomie du TP3 pour trouver où le signal passe sous le seuil."""
    debut = 0
    fin = 10

    while fin - debut > tolerance:
        milieu = (debut + fin) / 2

        if qualite_signal(milieu) >= seuil:
            debut = milieu
        else:
            fin = milieu

    return debut, fin


# La borne choisit le point où la qualité atteint le seuil demandé.
limite_basse, limite_haute = chercher_portee(seuil_signal)
portee = (limite_basse + limite_haute) / 2


def aire_polygone(polygone):
    """Calcule l'aire avec la formule du lacet vue en géométrie."""
    somme = 0
    for i in range(len(polygone)):
        suivant = (i + 1) % len(polygone)
        somme = somme + polygone[i][0] * polygone[suivant][1]
        somme = somme - polygone[suivant][0] * polygone[i][1]
    return abs(somme) / 2


def point_dans_cour(point, polygone):
    """Dit si un point est dans la cour avec le lancer de rayon du TP6."""
    x = point[0]
    y = point[1]
    dedans = False

    for i in range(len(polygone)):
        j = (i + 1) % len(polygone)
        x1 = polygone[i][0]
        y1 = polygone[i][1]
        x2 = polygone[j][0]
        y2 = polygone[j][1]

        # Un point exactement sur un côté compte comme étant dans la cour.
        determinant = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
        if abs(determinant) < 0.0000001:
            if x1 <= x2:
                entre_x = x1 <= x <= x2
            else:
                entre_x = x2 <= x <= x1
            if y1 <= y2:
                entre_y = y1 <= y <= y2
            else:
                entre_y = y2 <= y <= y1
            if entre_x and entre_y:
                return True

        # On compte les côtés que traverse un rayon horizontal vers la droite.
        if (y1 > y) != (y2 > y):
            x_croisement = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < x_croisement:
                dedans = not dedans

    return dedans


def distance(point_a, point_b):
    """Calcule la distance entre deux points avec le théorème de Pythagore."""
    difference_x = point_a[0] - point_b[0]
    difference_y = point_a[1] - point_b[1]
    return math.sqrt(difference_x * difference_x + difference_y * difference_y)


def wifi_passe(point, bornes):
    """Renvoie True si une borne est assez proche du point."""
    for borne in bornes:
        if qualite_signal(distance(point, borne)) >= seuil_signal:
            return True
    return False


def points_de_la_cour(pas_grille):
    """Place une grille de petits points et garde ceux dans la cour."""
    liste_points = []
    x = pas_grille / 2
    while x < 12:
        y = pas_grille / 2
        while y < 10:
            point = (x, y)
            if point_dans_cour(point, cour):
                liste_points.append(point)
            y = y + pas_grille
        x = x + pas_grille

    return liste_points


def pourcentage_couvert(liste_points, bornes):
    """Compte les points où le Wi-Fi passe et renvoie le pourcentage."""
    nombre_couvert = 0
    for point in liste_points:
        if wifi_passe(point, bornes):
            nombre_couvert = nombre_couvert + 1
    return 100 * nombre_couvert / len(liste_points)


def dessiner_plan(zone_dessin, liste_points, bornes, titre):
    """Dessine la cour, les zones couvertes et les bornes."""
    coins_x = []
    coins_y = []
    for coin in cour:
        coins_x.append(coin[0])
        coins_y.append(coin[1])

    # Dessine le fond de la cour.
    zone_dessin.fill(coins_x, coins_y, color="#eeeeee")

    # Sépare les points en deux listes pour colorier la couverture.
    x_wifi = []
    y_wifi = []
    x_sans_wifi = []
    y_sans_wifi = []
    for point in liste_points:
        if wifi_passe(point, bornes):
            x_wifi.append(point[0])
            y_wifi.append(point[1])
        else:
            x_sans_wifi.append(point[0])
            y_sans_wifi.append(point[1])

    zone_dessin.scatter(x_wifi, y_wifi, color="#2ecc71", s=12, label="Wi-Fi détecté")
    zone_dessin.scatter(x_sans_wifi, y_sans_wifi, color="#e74c3c", s=12, label="Pas de Wi-Fi")

    # La portée est tracée avec 40 petits segments qui forment un cercle.
    for i in range(len(bornes)):
        borne = bornes[i]
        cercle_x = []
        cercle_y = []
        for j in range(41):
            angle = 2 * math.pi * j / 40
            cercle_x.append(borne[0] + portee * math.cos(angle))
            cercle_y.append(borne[1] + portee * math.sin(angle))
        if i == 0:
            zone_dessin.plot(cercle_x, cercle_y, color="#3498db", linewidth=2,
                             label="Portée d'une borne")
        else:
            zone_dessin.plot(cercle_x, cercle_y, color="#3498db", linewidth=2)
        zone_dessin.scatter(borne[0], borne[1], color="#174a70", marker="^", s=90)

    zone_dessin.set_title(titre)
    zone_dessin.set_xlim(-0.5, 12.5)
    zone_dessin.set_ylim(-0.5, 10.5)
    zone_dessin.set_aspect("equal")
    zone_dessin.set_xlabel("x")
    zone_dessin.set_ylabel("y")
    zone_dessin.grid(True, alpha=0.2)
    zone_dessin.legend(loc="upper right", fontsize=8)


# TP2 : on compare le temps de calcul avec trois tailles de grille.
# Une grille plus petite contient davantage de points et demande plus de calculs.
print("Temps selon la finesse de la grille :")
for pas_test in [0.5, 0.2, 0.1]:
    debut_temps = time.perf_counter()
    points_test = points_de_la_cour(pas_test)
    score_test = pourcentage_couvert(points_test, placement_propose)
    temps = time.perf_counter() - debut_temps
    aire_estimee = len(points_test) * pas_test * pas_test
    print("Pas :", pas_test,
          "| points :", len(points_test),
          "| aire estimée :", round(aire_estimee, 1),
          "| couverture proposée :", round(score_test, 1), "%",
          "| temps :", round(temps, 3), "s")

# Le programme prépare les points de la carte, calcule les pourcentages,
# puis dessine les deux placements pour les comparer.
points_carte = points_de_la_cour(pas)

surface = aire_polygone(cour)
score_depart = pourcentage_couvert(points_carte, placement_depart)
score_propose = pourcentage_couvert(points_carte, placement_propose)

print("Surface de la cour :", surface, "unités carrées")
print("Seuil de qualité du signal :", seuil_signal, "%")
print("Portée estimée par dichotomie : entre", round(limite_basse, 2),
      "et", round(limite_haute, 2), "unités")
print("Qualité calculée au milieu de cette portée :", round(qualite_signal(portee), 1), "%")
print("Wi-Fi avec le placement de départ :", round(score_depart, 1), "%")
print("Wi-Fi avec le placement proposé :", round(score_propose, 1), "%")

figure, axes = plt.subplots(1, 2, figsize=(12, 5))
dessiner_plan(axes[0], points_carte, placement_depart, "Placement de départ")
dessiner_plan(axes[1], points_carte, placement_propose, "Placement proposé")
figure.suptitle("Où placer les bornes Wi-Fi ?")
figure.tight_layout()
figure.savefig("carte_wifi.png", dpi=150)
plt.show()
