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
### Étape (1/4) : Installation des prérequis. 
```
sudo ./requirement.sh
```
Ce script bash sert à mettre à jour votre Raspberry et installe les bibliothèques nécessaires.
 
### Étape (2/4) : Création de l'environnement Python
```
python3 -m venv .venv
```
```
source ./.venv/bin/activate
```
### Étape (3/4) : Installation des paquets requis (Environnement requis)
```
pip3 install bleak Pillow pygame pigpio
```

### Étape (4/4) Configuration de la télécommande
```
python3 IRCODENEC.py
```
Vous avez la possibilité d'utiliser n'importe quelle télécommande NEC.

<img width="300" height="300" alt="IMG_3090-removebg-preview" src="https://github.com/user-attachments/assets/325abebb-1d77-4c28-a8da-9433535a4e87" />

**Lorsque le dispositif IR est configuré, lancez ce programme qui vous permettra d'avoir les codes NEC en appuyant sur une touche de votre télécommande.**

<img width="631" height="186" alt="Code NEC" src="https://github.com/user-attachments/assets/183f444b-aaae-4ebb-9470-552403468d7f" />

### Lancement du programme
```
python3 ./IRCMRPi.py
```
# Présentation du programme

### Ecran d'acceuil du programme

<img width="850" height="687" alt="Ecran d'acceuil" src="https://github.com/user-attachments/assets/51150c27-c7b6-4f46-ae95-89002a6d2cdd" />

Le programme propose :
- Un mode Télécommande I
- Un mode clavier
- Un mode Console

Sélectionnez le mode qui vous convient en appuyant sur la touche "Entrer" de votre clavier.

**Aucun souci si vous n'avez pas de télécommande IR, utilisez votre clavier (Flèche du haut et flèche du bas) !**

# Mode Télécommande IR (Vidéo de test)

https://drive.google.com/file/d/1UK4dXc6K4iTbgxIoJfFUBS6DqsXQRXYX/view?usp=sharing

# Mode Clavier 

<img width="850" height="687" alt="Mode Clavier" src="https://github.com/user-attachments/assets/9b3c2485-b9c2-443e-b979-9509a3bbfb8a" />

# Mode Console

<img width="712" height="226" alt="Mode Console" src="https://github.com/user-attachments/assets/1103005d-dc53-4191-931c-2c6093198f2e" />




