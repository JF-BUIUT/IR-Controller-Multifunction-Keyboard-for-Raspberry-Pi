# Contrôleur infrarouge multifonction pour Raspberry Pi

Ce code est un programme complet pour **Raspberry Pi** qui transforme l'appareil en un **contrôleur multimédia et domotique interactif**.

Il sert principalement à afficher des informations sur un écran (connecté au Raspberry Pi) et à piloter ces affichages via deux méthodes d'entrée : une **télécommande infrarouge (IR)** ou un **clavier**.

Voici ses 4 fonctionnalités principales détaillées :

### 1. Affichage d'Images 
* **Fonction :** Affiche des images spécifiques en plein écran.
* **Utilisation :** Vous appuyez sur 1, 2 ou 3 (sur la télécommande ou le clavier) et le programme charge l'image associée.

### 2. Station Météo via Capteur DHT11 
* **Fonction :** Lit la température et l'humidité ambiante.
* **Fonctionnement :**
    * Il interroge un capteur physique **DHT11**.
    * Si le capteur ne répond pas (ou n'est pas branché), il passe en "mode simulation" et affiche des valeurs aléatoires pour tester l'interface.
    * Il affiche les résultats avec un code couleur (rouge si chaud, bleu si humide, etc.).

### 3. Scanner Bluetooth (BLE) 
* **Fonction :** Recherche des périphériques Bluetooth Low Energy (BLE) environnants.
* **Cible :** Il cherche spécifiquement l'appareil que vous souhaitez. (configurable).
* **Affichage :** S'il capte les données de cet appareil, il les affiche en temps réel sur l'écran.

### 4. (Bonus) Jeu "Snake" 
* **Fonction :** Lance un mini-jeu Snake classique.
* **Contrôle :** Le serpent se dirige avec les flèches directionnelles (Haut, Bas, Gauche, Droite) de la télécommande ou du clavier.

### Résumé Technique
* **Matériel géré :**
    * **IR (Infrarouge) :** Utilise la bibliothèque `pigpio` pour décoder les signaux d'une télécommande.
    * **Affichage :** Utilise `pygame` pour créer l'interface graphique.
    * **Capteur :** Gère le protocole temporel précis du DHT11 via `pigpio`.
* **Structure :** Le code est adaptable. Il détecte automatiquement si les bibliothèques sont installées (si `pigpio` manque, il désactive l'IR mais garde le clavier). Au démarrage, un menu vous demande quel mode de contrôle vous souhaitez utiliser.

⚠️ DISCLAIMER ⚠️
Je vous conseille de lire le manuel matériel avant la configuration du Raspberry Pi.

## ⬇️ Pour accéder au manuel des matériels utilisé ⬇️

### <a href="https://github.com/JF-BUIUT/IR-Controller-Multifunction-Keyboard-for-Raspberry-Pi/blob/main/Manuel-materiels.md">Manuel des matériels</a>

## ⬇️ Pour accéder à la configuration du Raspberry Pi & des dispositifs ⬇️

### <a href="https://github.com/JF-BUIUT/IR-Controller-Multifunction-Keyboard-for-Raspberry-Pi/blob/main/Configuration-Raspberry-Pi.md">Configuration générale du Raspberry Pi & des dispositifs (DH11, Télécommande,...)</a>
