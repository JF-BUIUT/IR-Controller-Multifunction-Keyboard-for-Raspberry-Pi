#!/usr/bin/env python3
"""
Contrôleur IR/Clavier multifonction pour Raspberry Pi
Menu au démarrage pour choisir le mode d'entrée
"""

import os
import sys
import time
import random
import subprocess
import threading
import asyncio
import queue
from datetime import datetime
from pathlib import Path

# --- Gestion unique de pigpio (IR + DHT) ---
try:
    import pigpio
    PIGPIO_AVAILABLE = True
    # On considère que si pigpio est là, IR et DHT sont dispo potentiellement
    IR_AVAILABLE = True 
    DHT_AVAILABLE = True 
except ImportError:
    print("Pigpio non disponible. Télécommande et DHT désactivés.")
    print("Installez: sudo apt install python3-pigpio & pip3 install pigpio (Pour l'environnement Python)")
    PIGPIO_AVAILABLE = False
    IR_AVAILABLE = False
    DHT_AVAILABLE = False

# Import pour affichage graphique
try:
    import pygame
    from PIL import Image
    PYGAME_AVAILABLE = True
except ImportError:
    print("PyGame non disponible. Affichage désactivé.")
    print("Installez: sudo apt install python3-pygame & sudo apt install python3-pillow & pip3 install Pillow pygame (Pour l'environnement Python)")
    PYGAME_AVAILABLE = False

# Import pour BLE
try:
    from bleak import BleakScanner
    BLE_AVAILABLE = True
except ImportError:
    print("Bleak non disponible. BLE désactivé.")
    print("Installez: sudo apt install python3-bleak & pip3 install bleak (Pour l'environnement Python)")
    BLE_AVAILABLE = False

# ===== CONFIGURATION =====
# Chemin des images (à modifier selon vos fichiers)
IMAGE_PATHS = {
    '1': 'IMAGES/logo rt.jpg', # Image 1
    '2': 'IMAGES/RTmascot.jpg', # Image 2
    '3': 'IMAGES/RTvsGEII.jpeg', # Image 3
}

# Configuration DHT11
DHT_PIN = 27  # GPIO 27 (Remplacer si besoin)
DHT_SENSOR = None 

# Configuration BLE
BLE_CONFIG = {
    'target_name': "...", #  Remplacez '...' par le nom du dispositif BLE (Format attendu : "Nom-du-BLE|température|humidité")
    'interval': 5
}

# Configuration IR et Mapping
GPIO_IR = 18 # Broche de réception (BCM 18) (Remplacer si besoin)

# Remplacez les 0xFFFFFF par vos codes hexadécimaux obtenus avec le script IRCODENEC.py  
REMOTE_KEY_MAP = {
    0xFFFFFF: '1',  # Touche 1 (Image 1)
    0xFFFFFF: '2',  # Touche 2 (Image 2)
    0xFFFFFF: '3',  # Touche 3 (Image 3)
    0xFFFFFF: '4',  # Touche 4 (DHT)
    0xFFFFFF: '5',  # Touche 5 (BLE)
    0xFFFFFF: 'h',  # Touche Menu/Help
    0xFFFFFF: 'q',  # Touche Power/Quit
    
    # --- TOUCHE JEU SNAKE ---
    0xFFFFFF: '9',      # Touche 9 pour lancer le Snake
    0xFFFFFF: 'UP',     # Flèche Haut
    0xFFFFFF: 'DOWN',   # Flèche Bas
    0xFFFFFF: 'LEFT',   # Flèche Gauche
    0xFFFFFF: 'RIGHT',  # Flèche Droite
}

# ===== CLASSES ET FONCTIONS =====

# --- ImageDisplay ---
class ImageDisplay:
    """Gestion de l'affichage d'images plein écran"""
    
    def __init__(self):
        if not PYGAME_AVAILABLE:
            raise ImportError("PyGame non disponible")
            
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600),pygame.RESIZABLE) # Gérer ici la taille de la fenêtre.
        pygame.display.set_caption("Contrôleur IR Multimode") # Le titre de la fenêtre.
        self.clock = pygame.time.Clock()
        self.current_image = None
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        
    def display_image(self, image_path):
        """Affiche une image en plein écran"""
        if not os.path.exists(image_path):
            self.display_error(f"Image non trouvée: {image_path}") # Si l'image n'est pas trouvée par le programme.
            return
            
        try:
            image = pygame.image.load(image_path)
            screen_width, screen_height = self.screen.get_size()
            image = pygame.transform.scale(image, (screen_width, screen_height))
            
            self.screen.blit(image, (0, 0))
            
            # Afficher le nom du fichier en bas à droite
            filename = os.path.basename(image_path)
            info_text = self.small_font.render(f"Image: {filename}", True, (255, 255, 255))
            info_rect = info_text.get_rect(bottomright=(screen_width - 10, screen_height - 10))
            self.screen.blit(info_text, info_rect)
            
            pygame.display.flip()
            print(f"Image affichée: {image_path}")
            
        except Exception as e:
            self.display_error(f"Erreur image: {str(e)}")
    
    def display_dht_data(self, temperature, humidity, is_test=False):
        """Affiche les données DHT11"""
        self.screen.fill((0, 0, 0))  # Fond noir
        
        # Titre
        title = "  DONNÉES CAPTEUR DHT11"
        if is_test:
            title = "  DONNÉES DE TEST (DHT11 non disponible)"
        
        title_text = self.font.render(title, True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.screen.get_width()//2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Température
        temp_color = (255, 100, 100) if temperature > 30 else (100, 255, 100) if temperature > 20 else (100, 150, 255)
        temp_text = self.font.render(f" Température: {temperature:.1f} °C", True, temp_color)
        temp_rect = temp_text.get_rect(center=(self.screen.get_width()//2, 200))
        self.screen.blit(temp_text, temp_rect)
        
        # Humidité
        hum_color = (100, 100, 255) if humidity > 60 else (100, 255, 100) if humidity > 30 else (255, 200, 100)
        hum_text = self.font.render(f" Humidité: {humidity:.1f} %", True, hum_color)
        hum_rect = hum_text.get_rect(center=(self.screen.get_width()//2, 300))
        self.screen.blit(hum_text, hum_rect)
        
        # Message info
        info = "Appuyez sur une autre touche pour continuer"
        info_text = self.small_font.render(info, True, (200, 200, 200))
        info_rect = info_text.get_rect(center=(self.screen.get_width()//2, 450))
        self.screen.blit(info_text, info_rect)
        
        # Timestamp
        time_str = datetime.now().strftime("%H:%M:%S")
        time_text = self.small_font.render(f"Dernière lecture: {time_str}", True, (150, 150, 150))
        time_rect = time_text.get_rect(center=(self.screen.get_width()//2, 500))
        self.screen.blit(time_text, time_rect)
        
        pygame.display.flip()
        print(f"Données affichées: {temperature}°C, {humidity}%")

    def display_ble_data(self, name, temperature, humidity):
        """Affiche les données BLE reçues (CORRECTIF: Méthode ajoutée)"""
        self.screen.fill((0, 0, 50))  # Fond bleu nuit
        
        # Titre
        title = f"SCAN BLE: {name}"
        title_text = self.font.render(title, True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.screen.get_width()//2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Température
        temp_text = self.font.render(f" Température: {temperature:.1f} °C", True, (255, 200, 100))
        temp_rect = temp_text.get_rect(center=(self.screen.get_width()//2, 200))
        self.screen.blit(temp_text, temp_rect)
        
        # Humidité
        hum_text = self.font.render(f" Humidité: {humidity:.1f} %", True, (100, 200, 255))
        hum_rect = hum_text.get_rect(center=(self.screen.get_width()//2, 300))
        self.screen.blit(hum_text, hum_rect)
        
        # Info
        info = "Scan en cours... Appuyez sur une touche pour arrêter"
        info_text = self.small_font.render(info, True, (200, 200, 200))
        info_rect = info_text.get_rect(center=(self.screen.get_width()//2, 450))
        self.screen.blit(info_text, info_rect)
        
        # Timestamp
        time_str = datetime.now().strftime("%H:%M:%S")
        time_text = self.small_font.render(f"Reçu à: {time_str}", True, (150, 150, 150))
        time_rect = time_text.get_rect(center=(self.screen.get_width()//2, 500))
        self.screen.blit(time_text, time_rect)
        
        pygame.display.flip()
    
    def display_menu(self, title, options, selected=0):
        """Affiche un menu avec options"""
        self.screen.fill((30, 30, 50))  # Fond bleu foncé
        
        # Titre
        title_text = self.font.render(title, True, (255, 255, 200))
        title_rect = title_text.get_rect(center=(self.screen.get_width()//2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Options
        y_pos = 200
        for i, (option, description) in enumerate(options):
            color = (255, 255, 100) if i == selected else (200, 200, 255)
            option_text = self.font.render(f"{i+1}. {option}", True, color)
            option_rect = option_text.get_rect(center=(self.screen.get_width()//2, y_pos))
            self.screen.blit(option_text, option_rect)
            
            if description:
                desc_text = self.small_font.render(description, True, (180, 180, 180))
                desc_rect = desc_text.get_rect(center=(self.screen.get_width()//2, y_pos + 30))
                self.screen.blit(desc_text, desc_rect)
                y_pos += 60
            else:
                y_pos += 50
        
        # Instructions
        instr_text = self.small_font.render("Utilisez flèche du (Haut) et flèche du (Bas) pour naviguer, ENTREE pour valider", True, (150, 150, 150))
        instr_rect = instr_text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height() - 50))
        self.screen.blit(instr_text, instr_rect)
        
        pygame.display.flip()
    
    def display_error(self, message):
        """Affiche un message d'erreur"""
        self.screen.fill((50, 0, 0))
        error_text = self.font.render(f"{message}", True, (255, 200, 200))
        error_rect = error_text.get_rect(center=(self.screen.get_width()//2, 
                                               self.screen.get_height()//2))
        self.screen.blit(error_text, error_rect)
        pygame.display.flip()
        print(f"Erreur: {message}")
    
    def display_info(self, message):
        """Affiche un message d'information"""
        self.screen.fill((0, 30, 0))
        info_text = self.font.render(message, True, (200, 255, 200))
        info_rect = info_text.get_rect(center=(self.screen.get_width()//2,
                                             self.screen.get_height()//2))
        self.screen.blit(info_text, info_rect)
        pygame.display.flip()
    
    def clear_screen(self):
        """Efface l'écran"""
        self.screen.fill((0, 0, 0))
        pygame.display.flip()
    
    def close(self):
        """Ferme proprement Pygame"""
        pygame.quit()

# --- DHT11Reader ---
class DHT11Reader:
    """Lecture des données du capteur DHT11 via PIGPIO"""
    
    def __init__(self, pin, sensor_type=None):
        self.pin = pin
        self.sensor_type = sensor_type # Gardé pour compatibilité signature mais non utilisé
        self.last_reading = None
        self.pi = None
        self.high_ticks = []
        self.last_tick = 0
        
        # Connexion pigpio
        if PIGPIO_AVAILABLE:
            self.pi = pigpio.pi()
            if not self.pi.connected:
                print("Impossible de connecter à pigpio daemon pour DHT")
                self.pi = None

    def _cb_dht(self, gpio, level, tick):
        """Callback interne pour mesurer les durées d'impulsion"""
        if level == 1: # Front montant (fin de l'état bas)
            self.last_tick = tick
        elif level == 0: # Front descendant (fin de l'état haut)
            if self.last_tick != 0:
                diff = pigpio.tickDiff(self.last_tick, tick)
                self.high_ticks.append(diff)

    def read(self):
        """Lit les données du capteur manuellement avec pigpio"""
        if not DHT_AVAILABLE or self.pi is None or not self.pi.connected:
            print("Pigpio/DHT non disponible - Valeurs de test")
            return self._return_test_values()

        try:
            self.high_ticks = []
            self.last_tick = 0
            
            # 1. Signal de démarrage (MCU tire vers le bas > 18ms)
            self.pi.set_mode(self.pin, pigpio.OUTPUT)
            self.pi.write(self.pin, 0)
            time.sleep(0.018) 
            
            # 2. Relâcher le bus (Pull up) et passer en écoute
            self.pi.set_mode(self.pin, pigpio.INPUT)
            self.pi.set_pull_up_down(self.pin, pigpio.PUD_UP)
            
            # 3. Enregistrer les transitions pendant 50ms (temps suffisant pour tout recevoir)
            cb_id = self.pi.callback(self.pin, pigpio.EITHER_EDGE, self._cb_dht)
            time.sleep(0.05)
            cb_id.cancel()
            
            # 4. Décoder les données
            # On ignore généralement les premiers ticks (réponse du capteur)
            # On cherche 40 bits de données
            data_bits = []
            
            # Les pulses de données : '0' (~26-28us HIGH), '1' (~70us HIGH)
            # On utilise un seuil à ~40us
            valid_pulses = [x for x in self.high_ticks if x > 10] # Filtre bruit
            
            # On s'attend à voir la réponse initiale puis 40 bits
            if len(valid_pulses) >= 40:
                # On prend les 40 derniers pulses qui correspondent aux données
                data_pulses = valid_pulses[-40:]
                
                for width in data_pulses:
                    if width > 40: # C'est un 1
                        data_bits.append(1)
                    else:          # C'est un 0
                        data_bits.append(0)
                
                # Convertir en octets
                bytes_data = [0, 0, 0, 0, 0]
                for i in range(40):
                    byte_idx = i // 8
                    bytes_data[byte_idx] = (bytes_data[byte_idx] << 1) | data_bits[i]
                
                # Vérifier le checksum
                # DHT11 format: IntRH, DecRH, IntT, DecT, Checksum
                checksum = (bytes_data[0] + bytes_data[1] + bytes_data[2] + bytes_data[3]) & 0xFF
                
                if bytes_data[4] == checksum:
                    humidity = float(bytes_data[0]) + float(bytes_data[1])/10.0
                    temperature = float(bytes_data[2]) + float(bytes_data[3])/10.0
                    
                    # Correction pour DHT11 standard qui n'a parfois pas de décimale
                    if self.sensor_type is None: # Comportement générique
                        pass 
                        
                    print(f"DHT11 (Pigpio): {temperature:.1f}°C, {humidity:.1f}%")
                    return temperature, humidity, False
                else:
                    raise Exception("Checksum invalide")
            else:
                raise Exception("Pas assez de données reçues")

        except Exception as e:
            print(f"Erreur lecture DHT (Pigpio): {str(e)}")
            return self._return_test_values()
            
    def _return_test_values(self):
        """Retourne des valeurs aléatoires pour le test"""
        temperature = round(random.uniform(18.0, 25.0), 1)
        humidity = round(random.uniform(40.0, 70.0), 1)
        self.last_reading = (temperature, humidity)
        return temperature, humidity, True

# --- BLEMonitor ---
class BLEMonitor:
    """Monitoring BLE avec File d'attente """
    def __init__(self, target_name, interval=5):
        self.target_name = target_name
        self.interval = interval
        self.running = False
        self.thread = None
        # Création d'une file d'attente pour communiquer avec l'affichage principal
        self.data_queue = queue.Queue()
        
    async def _monitor(self):
        if not BLE_AVAILABLE: return
        print(f"BLE Scan démarré pour: {self.target_name}")
        
        while self.running:
            try:
                devices = await BleakScanner.discover(timeout=3)
                found = False
                for d in devices:
                    if d.name and self.target_name in d.name:
                        found = True
                        try:
                            parts = d.name.split('|')
                            if len(parts) == 5:
                                temp = float(parts[1])
                                hum = float(parts[2])
                                name = parts[0]
                                # Au lieu de print, on met dans la file d'attente
                                self.data_queue.put((name, temp, hum))
                                print(f"Donnée reçue: {temp}°C {hum}%")
                        except:
                            pass
                        break
                if not found:
                    print(".", end="", flush=True) # Indicateur de vie console
            except Exception as e:
                print(f"Err BLE: {e}")
            await asyncio.sleep(self.interval)
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=lambda: asyncio.run(self._monitor()), daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False

# --- JEU SNAKE ---
class SnakeGame:
    """Jeu du Snake simple intégré"""
    def __init__(self, display):
        self.display = display
        self.block_size = 20
        self.width = 800
        self.height = 600
        # Couleurs
        self.c_bg = (0, 0, 0)
        self.c_snake = (0, 255, 0)
        self.c_food = (255, 0, 0)
        self.c_text = (255, 255, 255)
        
    def run_game(self, input_controller_ref):
        """Boucle principale du jeu Snake"""
        print("Démarrage du Snake...")
        
        # Init variables
        game_over = False
        x = self.width / 2
        y = self.height / 2
        
        x_change = 0
        y_change = 0
        
        snake_list = []
        snake_length = 1
        
        # Nourriture
        foodx = round(random.randrange(0, self.width - self.block_size) / 20.0) * 20.0
        foody = round(random.randrange(0, self.height - self.block_size) / 20.0) * 20.0
        
        clock = pygame.time.Clock()
        
        while not game_over:
            # 1. Gestion des entrées (IR et Clavier unifié)
            # On vérifie les inputs disponibles
            action = input_controller_ref._get_input_action()
            
            if action == 'q':
                return # Quitter le jeu
            elif action == 'LEFT' and x_change == 0:
                x_change = -self.block_size
                y_change = 0
            elif action == 'RIGHT' and x_change == 0:
                x_change = self.block_size
                y_change = 0
            elif action == 'UP' and y_change == 0:
                y_change = -self.block_size
                x_change = 0
            elif action == 'DOWN' and y_change == 0:
                y_change = self.block_size
                x_change = 0
            
            # 2. Logique de mouvement
            x += x_change
            y += y_change
            
            # Limites écran
            if x >= self.width or x < 0 or y >= self.height or y < 0:
                self.show_message("Game Over! Appuyez sur Q", (255, 0, 0))
                time.sleep(2)
                return
            
            self.display.screen.fill(self.c_bg)
            
            # Dessin Pomme
            pygame.draw.rect(self.display.screen, self.c_food, [foodx, foody, self.block_size, self.block_size])
            
            # Dessin Snake
            snake_head = []
            snake_head.append(x)
            snake_head.append(y)
            snake_list.append(snake_head)
            
            if len(snake_list) > snake_length:
                del snake_list[0]
                
            # Collision avec soi-même
            for x_segment in snake_list[:-1]:
                if x_segment == snake_head:
                    self.show_message("Game Over! Appuyez sur Q", (255, 0, 0))
                    time.sleep(2)
                    return
            
            self.draw_snake(snake_list)
            self.show_score(snake_length - 1)
            pygame.display.update()
            
            # Manger la pomme
            if x == foodx and y == foody:
                foodx = round(random.randrange(0, self.width - self.block_size) / 20.0) * 20.0
                foody = round(random.randrange(0, self.height - self.block_size) / 20.0) * 20.0
                snake_length += 1
                
            clock.tick(10) # Vitesse du serpent
            
    def draw_snake(self, snake_list):
        for x in snake_list:
            pygame.draw.rect(self.display.screen, self.c_snake, [x[0], x[1], self.block_size, self.block_size])
            
    def show_message(self, msg, color):
        mesg = self.display.font.render(msg, True, color)
        rect = mesg.get_rect(center=(self.width/2, self.height/2))
        self.display.screen.blit(mesg, rect)
        pygame.display.update()
        
    def show_score(self, score):
        value = self.display.small_font.render("Score: " + str(score), True, self.c_text)
        self.display.screen.blit(value, [0, 0])

# --- INPUT CONTROLLER ---
class InputController:
    """Contrôleur abstrait pour les entrées"""
    
    def __init__(self, display, dht_reader, ble_monitor):
        self.display = display
        self.dht_reader = dht_reader
        self.ble_monitor = ble_monitor
        self.ble_active = False
        self.running = True
        self.snake_game = SnakeGame(display)
        
    def handle_key(self, key):
        """Traite les touches (à implémenter par les sous-classes)"""
        raise NotImplementedError
        
    def run(self):
        """Boucle principale (à implémenter par les sous-classes)"""
        raise NotImplementedError
        
    def cleanup(self):
        """Nettoyage"""
        if self.ble_active:
            self.ble_monitor.stop()
        self.display.clear_screen()
        
    def _check_any_key_press(self):
        """Vérifie si une touche est pressée (Clavier ou IR)"""
        # 1. Vérification Clavier
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN or event.type == pygame.QUIT:
                return True
        
        # 2. Vérification IR (Si file d'attente existante)
        if hasattr(self, 'code_queue') and not self.code_queue.empty():
            try:
                self.code_queue.get_nowait() # On consomme l'événement
                return True
            except queue.Empty:
                pass
        
        return False

    def _get_input_action(self):
        """Récupère la prochaine action (Clavier ou IR) pour le jeu"""
        # 1. Clavier
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return 'q'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP: return 'UP'
                elif event.key == pygame.K_DOWN: return 'DOWN'
                elif event.key == pygame.K_LEFT: return 'LEFT'
                elif event.key == pygame.K_RIGHT: return 'RIGHT'
                elif event.key == pygame.K_q: return 'q'
        
        # 2. IR (si disponible)
        if hasattr(self, 'code_queue'):
            try:
                # On ne bloque pas pour ne pas figer le jeu
                code = self.code_queue.get_nowait()
                if code in REMOTE_KEY_MAP:
                    return REMOTE_KEY_MAP[code]
            except queue.Empty:
                pass
        
        return None

    def process_command(self, key):
        """Traite une commande (commun aux deux modes)"""
        print(f"Commande: {key}")
        
        # Arrêter le monitoring BLE si actif
        if self.ble_active:
            self.ble_monitor.stop()
            self.ble_active = False
            time.sleep(1)
        
        if key in ['1', '2', '3']: # Touche des images
            # Afficher l'image correspondante
            image_path = IMAGE_PATHS.get(key)
            if image_path and os.path.exists(image_path):
                self.display.display_image(image_path)
            else:
                self.display.display_error(f"Image non trouvée pour {key}")
                
        elif key == '4': # Touche 4 du clavier
            # Lire et afficher données DHT11 avec timeout de 5s
            start = time.time()
            temperature = humidity = None
            is_test = False

            while time.time() - start < 1:
                t, h, test = self.dht_reader.read()
                if not test:   # vraie donnée
                    temperature, humidity, is_test = t, h, False
                    break
                time.sleep(0.5)

            # Si aucune donnée réelle après le timeout → mode test en continu
            if temperature is None:
                print("Aucun signal DHT après attente → Mode test activé")
                is_test = True

                # boucle d’affichage test toutes les 3 secondes
                while True:
                    temperature = round(random.uniform(18.0, 25.0), 1)
                    humidity = round(random.uniform(40.0, 70.0), 1)

                    self.display.display_dht_data(temperature, humidity, True)

                    # sortir si une touche est pressée (clavier ou IR via queue)
                    if self._check_any_key_press():
                        return True
                    
                    time.sleep(3)

            # Affichage normal si donnée réelle obtenue
            self.display.display_dht_data(temperature, humidity, is_test)
      
            
        elif key == '5': # Touche 5 du clavier
            if not BLE_AVAILABLE:
                self.display.display_error("BLE non disponible")
                return True

            self.display.display_info("Démarrage BLE... (Patientez)")
            self.ble_monitor.start()
            
            # Boucle d'affichage dédiée au BLE (bloque le menu, affiche les data)
            in_ble_mode = True
            last_update = 0
            
            # On vide la file avant de commencer
            while not self.ble_monitor.data_queue.empty():
                self.ble_monitor.data_queue.get()

            while in_ble_mode:
                # 1. Vérifier si nouvelles données BLE
                try:
                    # On regarde la queue sans bloquer
                    data = self.ble_monitor.data_queue.get(block=False)
                    name, t, h = data
                    # CORRECTIF: Appel de la méthode display_ble_data qui manquait
                    self.display.display_ble_data(name, t, h)
                    last_update = time.time()
                except queue.Empty:
                    pass

                # 2. Gestion du timeout visuel (si pas de données)
                if time.time() - last_update > 10 and last_update != 0:
                     # Optionnel : afficher "Perte de signal" si besoin
                     pass

                # 3. Vérifier si l'utilisateur veut quitter (IR ou Clavier)
                if self._check_any_key_press():
                    in_ble_mode = False
                
                time.sleep(0.1)
            
            # Arrêt du monitoring quand on quitte l'écran
            self.ble_monitor.stop()
            self.display.display_info("Arrêt du monitoring BLE")
            time.sleep(1)
            self.display.clear_screen()
        
        # --- AJOUT COMMANDE SNAKE ---
        elif key == '9': #Touche 9 du clavier 
            self.snake_game.run_game(self)
            self.display.clear_screen()

        elif key in ['q', 'Q', 'escape']: return False # Quitter le jeu
        elif key == 'h': self.display_help() # Retourner au menu d'aide
        return True
    
    def display_help(self):
        """Affiche l'aide"""
        self.display.screen.fill((30, 30, 60))
        
        title_text = self.display.font.render("AIDE - TOUCHES DISPONIBLES", True, (255, 255, 200))
        title_rect = title_text.get_rect(center=(self.display.screen.get_width()//2, 80))
        self.display.screen.blit(title_text, title_rect)
        
        # Affichage du texte du menu aide  
        commands = [
            ("1, 2, 3", "Afficher différentes images"),
            ("4", "Afficher température/humidité (Interieur)"),
            ("5", "Lancer le monitoring BLE (Exterieur)"),
            ("9", "Jeu Snake (Easter egg)"),
            ("H (SETUP)", "Afficher le menu principal"),
            ("Q (STOP)", "Quitter le programme")
        ]
        
        y_pos = 150
        for key, desc in commands:
            key_text = self.display.font.render(key, True, (100, 255, 100))
            key_rect = key_text.get_rect(topleft=(200, y_pos))
            self.display.screen.blit(key_text, key_rect)
            
            desc_text = self.display.small_font.render(desc, True, (200, 200, 255))
            desc_rect = desc_text.get_rect(topleft=(350, y_pos + 5))
            self.display.screen.blit(desc_text, desc_rect)
            
            y_pos += 60
        
        # Instructions pour retour
        back_text = self.display.small_font.render("Appuyez sur n'importe quelle touche pour continuer", 
                                                  True, (150, 150, 150))
        back_rect = back_text.get_rect(center=(self.display.screen.get_width()//2, 
                                             self.display.screen.get_height() - 50))
        self.display.screen.blit(back_text, back_rect)
        
        pygame.display.flip()
        time.sleep(0.5)  # Petite pause pour éviter les appuis accidentels

# --- IR CONTROLLER ---
class IRController(InputController):
    """Contrôleur par télécommande IR utilisant PIGPIO"""
    
    def __init__(self, display, dht_reader, ble_monitor):
        super().__init__(display, dht_reader, ble_monitor)
        
        if not IR_AVAILABLE:
            raise ImportError("Pigpio non disponible")
            
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise ImportError("Impossible de se connecter à pigpiod")
            
        self.code_queue = queue.Queue()
        self.setup_ir_receiver()
        
    def setup_ir_receiver(self):
        """Initialise la réception NEC sur le GPIO"""
        self.pi.set_mode(GPIO_IR, pigpio.INPUT)
        self.pi.set_glitch_filter(GPIO_IR, 100)
        self.pi.callback(GPIO_IR, pigpio.EITHER_EDGE, self._cb)
        
        self.in_code = False
        self.code = 0
        self.bits = 0
        self.last_tick = 0
        print(f"Récepteur IR (Pigpio) actif sur GPIO {GPIO_IR}")

    def _cb(self, gpio, level, tick):
        """Callback bas niveau pour décoder le NEC"""
        if self.last_tick != 0:
            diff = pigpio.tickDiff(self.last_tick, tick)
            
            if 8000 < diff < 10000 and level == 1: # Header Start
                self.in_code = False
            elif 4000 < diff < 5000 and level == 0: # Header Space
                self.in_code = True; self.code = 0; self.bits = 0
            elif self.in_code and level == 0:
                if 400 < diff < 700: self.code = self.code << 1; self.bits += 1
                elif 1500 < diff < 1800: self.code = (self.code << 1) | 1; self.bits += 1
                else: self.in_code = False
                
                if self.bits == 32:
                    # Code reçu ! On l'ajoute à la file d'attente
                    self.code_queue.put(self.code)
                    self.in_code = False
        self.last_tick = tick

    def run(self):
        """Boucle principale de lecture des commandes IR."""
        print("IRController démarré – en attente de signaux IR…")
        
        self.display_help()

        try:
            while self.running:
                # 1. Vérifier si un code IR est arrivé dans la file d'attente
                try:
                    code = self.code_queue.get(timeout=0.1) # Attente non bloquante 100ms
                    
                    if code in REMOTE_KEY_MAP:
                        key = REMOTE_KEY_MAP[code]
                        print(f"Code IR: 0x{code:X} -> Touche '{key}'")
                        self.running = self.process_command(key)
                    else:
                        print(f"Code IR inconnu: 0x{code:X}") #Si la touche est mal configurée.
                        
                except queue.Empty:
                    pass
                
                # 2. Garder la fenêtre Pygame active (sinon elle gèle)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False

        except KeyboardInterrupt:
            print("Arrêt...")
        finally:
            self.pi.stop()
            print("IRController arrêté.")

# --- KEYBOARD CONTROLLER ---
class KeyboardController(InputController):
    """Contrôleur par clavier"""
    
    def __init__(self, display, dht_reader, ble_monitor):
        super().__init__(display, dht_reader, ble_monitor)
        
        # Initialiser Pygame pour les événements clavier
        pygame.display.init()
        print("Contrôle clavier initialisé")
    
    def run(self):
        """Boucle principale pour clavier"""
        print("\n" + "="*50)
        print("MODE CLAVIER ACTIVÉ")
        print("="*50)
        
        self.display_help()
        
        try:
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        break
                        
                    elif event.type == pygame.KEYDOWN:
                        key = self.get_key_name(event.key)
                        
                        if key:
                            self.running = self.process_command(key)
                
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print("\nInterruption manuelle")
        finally:
            self.cleanup()
    
    def get_key_name(self, key_code):
        """Convertit un code de touche en nom"""
        key_map = {
            pygame.K_1: '1', # Touche 1 du clavier (Image 1)
            pygame.K_2: '2', # Touche 2 du clavier (Image 2)
            pygame.K_3: '3', # Touche 3 du clavier (Image 3)
            pygame.K_4: '4', # Touche 4 du clavier (DH11)
            pygame.K_5: '5', # Touche 5 du clavier (BLE)
            pygame.K_9: '9', # Touche 9 du clavier (Jeu Snake)
            pygame.K_q: 'q', # Touche q du clavier (Quitter le programme)
            pygame.K_ESCAPE: 'escape', # Touche échap du clavier (Quitter le programme)
            pygame.K_h: 'h', # Touche 1 du clavier (Menu d'aide)
        }
        
        # Touches numériques du pavé numérique
        if pygame.K_KP1 <= key_code <= pygame.K_KP9:
            return str(key_code - pygame.K_KP1 + 1)
            
        return key_map.get(key_code, None)

# --- MAIN MENU ---
class MenuManager:
    """Gère le menu de sélection au démarrage"""
    
    def __init__(self):
        self.display = None
        self.selected_mode = None
        
    def init_display(self):
        """Initialise l'affichage"""
        if not PYGAME_AVAILABLE:
            print("PyGame non disponible - Mode console uniquement")
            return False
            
        try:
            self.display = ImageDisplay()
            return True
        except:
            print("Impossible d'initialiser l'affichage")
            return False
    
    def show_text_menu(self):
        """Affiche le menu en mode texte"""
        print("\n" + "="*50)
        print("MENU DE SÉLECTION - MODE D'ENTRÉE")
        print("="*50)
        print("1. Télécommande IR (Pigpio)")
        print("2. Clavier")
        print("3. Mode Console (sans affichage)")
        print("Q. Quitter")
        print("="*50)
        
        while True:
            choice = input("\nVotre choix (1-3, Q): ").strip().lower()
            
            if choice == '1': # Mode IR
                return 'ir'
            elif choice == '2': # Mode clavier
                return 'keyboard'
            elif choice == '3': # Mode console
                return 'console'
            elif choice in ['q', 'quit']: # Quitter
                return 'quit'
            else:
                print("Choix invalide. Réessayez.")
    
    def show_graphical_menu(self):
        """Affiche le menu en mode graphique"""
        options = [
            ("Télécommande IR", "Utilise la télécommande (Pigpio)"),
            ("Clavier", "Utilise le clavier de l'ordinateur"),
            ("Mode Console", "Sans affichage graphique"),
            ("Quitter", "Arrêter le programme")
        ]
        
        selected = 0
        self.display.display_menu("SÉLECTIONNEZ LE MODE D'ENTRÉE", options, selected)
        
        # Gestion des touches pour le menu
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(options)
                        self.display.display_menu("SÉLECTIONNEZ LE MODE D'ENTRÉE", options, selected)
                    elif event.key == pygame.K_UP:
                        selected = (selected - 1) % len(options)
                        self.display.display_menu("SÉLECTIONNEZ LE MODE D'ENTRÉE", options, selected)
                    elif event.key == pygame.K_RETURN:
                        waiting = False
                    elif event.key in [pygame.K_q, pygame.K_ESCAPE]:
                        return 'quit'
            
            time.sleep(0.05)
        
        # Retourne le choix
        if selected == 0:
            return 'ir'
        elif selected == 1:
            return 'keyboard'
        elif selected == 2:
            return 'console'
        else:
            return 'quit'
    
    def get_mode_selection(self):
        """Obtient la sélection de mode de l'utilisateur"""
        if self.init_display():
            return self.show_graphical_menu()
        else:
            return self.show_text_menu()

# --- Console Mode ---
class ConsoleMode:
    """Mode console uniquement (sans affichage graphique)"""
    
    def __init__(self):
        self.dht_reader = DHT11Reader(DHT_PIN, DHT_SENSOR)
        self.ble_monitor = BLEMonitor(**BLE_CONFIG)
        self.ble_active = False
        
    def run(self):
        """Exécute le mode console avec affichage pygame."""
        print("\n" + "="*50)
        print("MODE CONSOLE ACTIVÉ (Affichage d'images via Pygame)")
        print("="*50)
        print("Commandes disponibles:")
        print("  1, 2, 3 : Afficher le chemin de l'image (Affiche l'image dans l'interface graphique)")
        print("  4       : Lire le DHT11")
        print("  5       : Lancer le monitoring BLE")
        print("  h       : Afficher cette aide")
        print("  q       : Quitter")
        print("="*50)

        # On crée une fenêtre pygame pour afficher les images
        from pygame import display
        display.init()
        self.display = ImageDisplay()

        try:
            while True:
                cmd = input("\nCommande> ").strip().lower()

                if cmd in ['1', '2', '3']:
                    path = IMAGE_PATHS.get(cmd)
                    if path and os.path.exists(path):
                        self.display.display_image(path)
                    else:
                        print(f"Image introuvable : {path}")

                elif cmd == '4':
                    temp, hum, is_test = self.dht_reader.read()
                    self.display.display_dht_data(temp, hum, is_test)

                elif cmd == '5':
                    if self.ble_active:
                        self.ble_monitor.stop()
                    print("Lancement du monitoring BLE...")
                    self.ble_active = True
                    self.ble_monitor.start()

                elif cmd == 'h':
                    print("1,2,3 = images, 4 = DHT11, 5 = BLE, q = quitter")

                elif cmd in ['q', 'quit', 'exit']:
                    print("Au revoir!")
                    break

                else:
                    print("Commande inconnue.")

        except KeyboardInterrupt:
            print("\nAu revoir!")
        finally:
            if self.ble_active:
                self.ble_monitor.stop()


# ===== MAIN =====

def check_dependencies():
    """Vérifie les dépendances système"""
    print("Vérification des dépendances...")
    
    # Vérifier images
    for key, path in IMAGE_PATHS.items():
        if not os.path.exists(path):
            print(f"⚠️ Image manquante pour touche {key}: {path}")
            print(f"   Créez: touch {path}  # ou placez une vraie image")
    
    print("\nVérifications terminées")

def main():
    """Fonction principale"""
    print("\n" + "="*50)
    print("CONTRÔLEUR MULTIMODE RASPBERRY PI")
    print("="*50)
    
    # Assurez-vous que le démon pigpiod est lancé
    # os.system("sudo pigpiod") 
    
    check_dependencies()
    
    # Menu de sélection
    menu = MenuManager()
    mode = menu.get_mode_selection()
    
    if mode == 'quit':
        print("👋 Au revoir!")
        if menu.display:
            menu.display.close()
        return
    
    # Initialisation selon le mode choisi
    try:
        if mode == 'console':
            # Mode console uniquement
            console = ConsoleMode()
            console.run()
            
        else:
            # Modes avec affichage graphique
            if not PYGAME_AVAILABLE:
                print("PyGame requis pour ce mode. Passage en mode console.")
                console = ConsoleMode()
                console.run()
                return
            
            # Initialiser les composants
            display = ImageDisplay()
            dht_reader = DHT11Reader(DHT_PIN, DHT_SENSOR)
            ble_monitor = BLEMonitor(**BLE_CONFIG)
            
            # Créer le contrôleur approprié
            if mode == 'ir':
                if not IR_AVAILABLE:
                    print("PIGPIO non disponible. Passage en mode clavier.")
                    mode = 'keyboard'
            
            if mode == 'ir':
                controller = IRController(display, dht_reader, ble_monitor)
            else:  # keyboard
                controller = KeyboardController(display, dht_reader, ble_monitor)
            
            # Lancer le contrôleur
            controller.run()
            
    except Exception as e:
        print(f"\nErreur critique: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nProgramme terminé")

if __name__ == "__main__":
    main()
