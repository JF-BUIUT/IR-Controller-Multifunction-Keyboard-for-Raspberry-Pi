import pigpio
import time
import sys

# --- CONFIGURATION ---
# Remplacez par le numéro BCM du GPIO où est branché le RX du SBC-IRC389
GPIO_RX = 18 

class IRDecoder:
    def __init__(self, pi, gpio):
        self.pi = pi
        self.gpio = gpio
        self.code = 0
        self.in_code = False
        self.last_tick = 0
        self.bits = 0
        self.t0 = 0

        # Configuration du GPIO en entrée
        self.pi.set_mode(gpio, pigpio.INPUT)
        self.pi.set_glitch_filter(gpio, 100) # Filtre les bruits < 100µs

        # On écoute les changements d'état (montant ou descendant)
        self.cb = self.pi.callback(gpio, pigpio.EITHER_EDGE, self._cb)
        print(f"Écoute sur le GPIO {gpio}...")

    def _cb(self, gpio, level, tick):
        # Calcul de la durée de l'impulsion (en microsecondes)
        if self.last_tick != 0:
            diff = pigpio.tickDiff(self.last_tick, tick)
            
            # --- LOGIQUE DE DÉTECTION NEC ---
            # Le protocole NEC commence par un entête :
            # 9ms (9000µs) pulse + 4.5ms (4500µs) space
            
            # Détection de l'entête (Header) avec une tolérance
            if 8000 < diff < 10000 and level == 1: # Fin du pulse 9ms
                self.in_code = False # Reset
            elif 4000 < diff < 5000 and level == 0: # Fin de l'espace 4.5ms
                # C'est un début de code NEC valide !
                self.in_code = True
                self.code = 0
                self.bits = 0
                # print("  -> Début de trame NEC détecté")
            
            elif self.in_code:
                # Lecture des bits
                # Bit 0 : Pulse 560µs + Espace 560µs (~1120µs total)
                # Bit 1 : Pulse 560µs + Espace 1690µs (~2250µs total)
                
                # On s'intéresse à la durée entre deux fronts descendants (période complète)
                # Mais ici on simplifie en regardant la durée de l'espace précédent
                if level == 0: # On vient de finir un espace
                    if 400 < diff < 700:
                        # C'est un 0 (espace court)
                        self.code = self.code << 1
                        self.bits += 1
                    elif 1500 < diff < 1800:
                        # C'est un 1 (espace long)
                        self.code = (self.code << 1) | 1
                        self.bits += 1
                    else:
                        # Erreur de timing, on arrête
                        self.in_code = False

                    # Un code NEC standard fait 32 bits
                    if self.bits == 32:
                        print(f"NEC REÇU : Hex=0x{self.code:08X} | Dec={self.code}")
                        self.in_code = False
            
            # --- MODE BRUT (DEBUG) ---
            # Si ce n'est pas du NEC standard, on affiche quand même qu'il se passe quelque chose
            # pour confirmer que le capteur marche (Sony/RC5 s'afficheront ici)
            elif diff > 1000 and diff < 3000:
                # Si on voit des impulsions de 1 à 3ms, c'est probablement du Sony ou RC5
                # On n'affiche pas tout pour ne pas spammer, juste un point
                print(".", end="", flush=True)

        self.last_tick = tick

def main():
    pi = pigpio.pi()
    if not pi.connected:
        print("Impossible de se connecter au démon pigpio.")
        print("Avez-vous lancé 'sudo pigpiod' ?")
        sys.exit()

    try:
        decoder = IRDecoder(pi, GPIO_RX)
        print(" Appuyez sur les touches de votre télécommande...")
        print("(Si des points '...' s'affichent, c'est que le signal est reçu mais non-NEC)")
        
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nArrêt...")
        pi.stop()

if __name__ == "__main__":
    main()
