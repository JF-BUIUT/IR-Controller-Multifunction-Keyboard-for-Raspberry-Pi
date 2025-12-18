# Configuration requise (sous Linux)

## Installation
```
https://github.com/JF-BUIUT/Controleur-IR-multifonction-RPi.git
cd IR-Controller-Multifunction-Keyboard-for-Raspberry-Pi
chmod +x ./requirement.sh
```
Si vous obtenez l'erreur : La commande « git » n'a pas été trouvée. Vous pouvez l'installer en tapant la commande : 
```
sudo apt install git
```
### Étape [1/4] : Installation des prérequis. 
```
sudo ./requirement.sh
```
Ce script bash sert à mettre à jour votre Raspberry et installe les bibliothèques nécessaires.
 
### Étape [2/4] :Création de l'environnement Python
```
python3 -m venv .venv
```
```
source ./.venv/bin/activate
```
### Étape [3/4] : Installation des paquets requis (Environement requis)
```
pip3 install bleak Pillow pygame pigpio
```

### Étape [4/4] : Lancement du programme
```
python3 ./IRCMRPi.py
```

# Présentation du programme



