#!/bin/bash
echo "====================================================="
echo "     INSTALLATION AUTOMATIQUE DES BIBLIOTHÈQUES"
echo "====================================================="

echo "[1/3] Mise à jour du Raspberry Pi..."
sudo apt autoremove
sudo apt update -y && sudo apt upgrade -y

echo "[2/3] Installation des paquets..."
sudo apt install python3-full 
sudo apt install python3.13-venv
sudo apt install python3-pip 
sudo apt install python3-pigpio 
sudo apt install python3-bleak
sudo apt install python3-pillow
sudo apt install python3-pygame
sudo apt install pipx

echo "[3/3] Création de l'environnement python..."
python3 -m venv setup 

echo "L'environnement python à bien été crée !"

echo "Lancer le avec '   source setup/bin/activate     ' "

