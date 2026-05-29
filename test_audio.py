import pygame
import time
import os

# # Setzt die Systemlautstärke auf 50%
# os.system("amixer sset Master 50%")


def play_sound(file_path):
    # Initialisiere das Sound-Modul
    pygame.mixer.init()
    # Lade die Sound-Datei
    sound = pygame.mixer.Sound(file_path)
    sound.set_volume(0.5)  # 10% Lautstärke
    
    # Spiele den Sound ab
    print("Spiele Ton ab...")
    sound.play()
    
    # Warte, bis der Ton zu Ende ist
    time.sleep(sound.get_length())
    print("Fertig.")

if __name__ == "__main__":
    # Du brauchst eine .wav Datei im gleichen Ordner
    # Eine einfache Piep-Datei reicht völlig aus
    print ("Spiele sound in 3..")
    time.sleep(1)
    print ("Spiele sound in 2..")
    time.sleep(1)
    print ("Spiele sound in 1..")
    time.sleep(1)
    print ("Los!")
    play_sound("beep-01a.wav")