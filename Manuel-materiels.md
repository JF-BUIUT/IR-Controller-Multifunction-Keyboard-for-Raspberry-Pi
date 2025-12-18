# Manuel des matériels

### Matériels et logiciels utilisés :
* Raspberry Pi Imager
* Raspberry Pi 3 Model B
* Une carte Micro SD (8-16 Go) & un adaptateur pour flasher la carte micro SD
* Capteur DH11
* Capteur IR (Infrarouge)
* Télécommande NEC

**⚠️ Pour ce tuto, j'ai utilisé un Raspberry Pi 3 Model B ⚠️**

## Étape 1 : Installation de L'OS
Sur un PC rendez-vous sur le site de Raspberry et installez Raspberry Pi Imager : https://www.raspberrypi.com/software/

<img width="600" height="400" alt="Raspberry Pi Imager" src="https://github.com/user-attachments/assets/1aa476f9-cbf8-4db9-8fd2-656743130475" />

Brancher l'adaptateur ainsi que la carte SD.

Sélectionner ensuite votre modèle de Raspberry Pi puis Raspberry Pi OS (other), ensuite sélectionner **Raspberry Pi OS FULL (32-Bit)**

<img width="440" height="105" alt="Raspberry Pi Imager" src="https://github.com/user-attachments/assets/d68888e5-05c8-4d06-b585-46c4d7f4853e" />

Configurer les paramètres du Raspberry et flashez-le.

## Étape 2 : Câblage du matériel

**⚠️ Rappel : selon le modèle de Raspberry que vous avez, les branchements diffèrent... ⚠️**

<img width="800" height="800" alt="RPi DataSheet Pinout" src="https://github.com/user-attachments/assets/37af9519-419b-4464-823e-22a2fc6da2f8" />

Source : https://www.14core.com/datasheets-pin-outs/raspberry-pi-gpio-pinouts-diagram/

**⚠️ Vous pouvez directement voir le datasheet du modèle de votre Raspberry Pi en tapant `pinout` dans le terminal ⚠️**

### Étape 2.1 : Câblage du capteur DH11 

<img width="400" height="400" alt="DH11" src="https://github.com/user-attachments/assets/ee20002e-2ee4-471d-8fbe-1b37f58bdb65" />

**VCC (+)** correspond à l'alimentation, **DATA/OUT** correspond à la sortie, **GND (-)** correspond à la masse.

### **Câblage recommandé**

**VCC (+)** = Pin 1 **(3V3)**

**DATA/OUT** = Pin 13 **(GPIO 27)**

**GND (-)** = Pin 6 **(GND)**

### Étape 2.2 : Câblage du capteur IR

<img width="400" height="400" alt="IR SENSOR" src="https://github.com/user-attachments/assets/cbb57f8a-a669-46df-b2e3-1518ec347e5c" />

**VCC (+)** correspond à l'alimentation, **DATA/OUT** correspond à la sortie, **GND (-)** correspond à la masse.

### **Câblage recommandé**

**VCC (+)** = Pin 4 **(5V)**

**DATA/OUT** = Pin 12 **(GPIO 18)**

**GND (-)** = Pin 14 **(GND)**

### **Montage final**

<img width="1239" height="922" alt="526366686-7dcd802f-1592-40c3-b669-fd65bbf3c435" src="https://github.com/user-attachments/assets/af7e51b3-4d91-46ef-8736-0c6390fcaacf" />


