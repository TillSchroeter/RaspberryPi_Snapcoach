import sys
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import QTimer, Qt
import pyqtgraph as pg
import numpy as np
import random
import time
from daqhats import hat_list, HatIDs, mcc128, AnalogInputRange, AnalogInputMode, OptionFlags
import pygame

from daten import probe_funktion
from main import measurement

### Boards initialisieren
board_list = hat_list(filter_by_id=HatIDs.MCC_128)
if not board_list:
    print("Kein Board gefunden!")
else:
    hat1 = mcc128(board_list[0].address)
    hat1.a_in_mode_write(AnalogInputMode.SE)
    hat1.a_in_range_write(AnalogInputRange.BIP_5V)

    hat2 = mcc128(board_list[1].address)
    hat2.a_in_mode_write(AnalogInputMode.SE)
    hat2.a_in_range_write(AnalogInputRange.BIP_5V)


### styles für die Status-Labels
style_grau = """color: #383d41; 
            background-color: #e2e3e5; 
            font-weight: bold;
            border: 1px solid #d6d8db;
            border-radius: 8px;
            padding: 5px; """
style_rot = """color: #721c24; 
            background-color: #f8d7da; 
            font-weight: bold;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            padding: 5px; """
style_grün ="""color: #155724; 
            background-color: #d4edda; 
            font-weight: bold;
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            padding: 5px;"""

### Hauptklasse für die Anwendung
class MeinPiProjekt(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Die UI-Datei laden
        uic.loadUi("app_GUI.ui", self)
        
        ### ploting
        # 1. Plot-Widgets erstellen
        self.pw_links = pg.PlotWidget()
        self.pw_rechts = pg.PlotWidget()

        # 2. Die Plot-Widgets in deine Designer-Widgets einbetten
        # Wir erstellen Layouts für deine Platzhalter-Widgets
        layout_l = QtWidgets.QVBoxLayout(self.plot_links)
        layout_r = QtWidgets.QVBoxLayout(self.plot_rechts)

        layout_l.addWidget(self.pw_links)
        layout_r.addWidget(self.pw_rechts)

        # 3. Optik anpassen (Weißer Hintergrund)
        self.pw_links.setBackground('w') # 'w' für weiß
        self.pw_rechts.setBackground('w')

        # Achsenfarben auf Schwarz setzen, damit sie auf weiß sichtbar sind
        self.pw_links.getAxis('left').setPen('k') # 'k' steht für schwarz
        self.pw_links.getAxis('bottom').setPen('k')
        self.pw_rechts.getAxis('left').setPen('k')
        self.pw_rechts.getAxis('bottom').setPen('k')

        # Achsen für den linken Plot beschriften
        self.pw_links.setLabel('left', 'F', units='N')      # Y-Achse: F in Newton
        self.pw_links.setLabel('bottom', 't', units='s')    # X-Achse: t in Sekunden

        # Achsen für den rechten Plot beschriften
        self.pw_rechts.setLabel('left', 'F', units='N')
        self.pw_rechts.setLabel('bottom', 't', units='s')

        # Titel-Farbe auf Schwarz ändern
        # self.pw_links.setTitle("Linke Hand - Kraft", color="k", size="12pt")
        # self.pw_rechts.setTitle("Rechte Hand - Kraft", color="k", size="12pt")

        ### Die Buttons mit Funktionen verbinden
        # Ersetze 'btn_start_messung' durch den objectName aus dem Designer
        self.btn_start_messung.clicked.connect(self.starte_messung)
        self.btn_neue_messung.clicked.connect(self.neue_messung)  # Beispiel: Beide Buttons starten die gleiche Funktion

        ### sound laden
        # Initialisiere das Sound-Modul
        pygame.mixer.init()
        self.sound = pygame.mixer.Sound("beep-01a.wav")

        # 0 = Erster Tab, 1 = Zweiter Tab
        self.tabWidget.setCurrentIndex(0)


    def starte_messung(self):
        # 1. Prüfen ob Trigger gewählt
        if not self.visuell.isChecked() and not self.akustisch.isChecked():
            self.status_mess_start.setText("Bitte Trigger wählen!")
            self.status_mess_start.setStyleSheet(style_rot)
            QTimer.singleShot(3000, lambda: self.reset_label(self.status_mess_start))
            return

        #Varablen
        vorbereitung = 750 #ms

        # 2. Vorbereitung: Status setzen
        self.status_mess_start.setText("Bereit machen...")
        self.status_mess_start.setStyleSheet(style_grau)

        # Timer starten: die Funktion 'reset_label' aufrufen
        QTimer.singleShot(vorbereitung, lambda: self.reset_label(self.status_mess_start))

        # Hebt den Frame über alle anderen Elemente
        self.signal_frame.raise_()

        # 3. Kette starten: Nach 0,75s wird das Bild WEISS (Vorbereitung für Athlet)
        QTimer.singleShot(vorbereitung, self.trigger_vorbereitung)

    def trigger_vorbereitung(self):
        # Ganzen Frame weiß machen
        self.signal_frame.setStyleSheet("background-color: white;")
        
        # 4. Zufallszeit zwischen 1000ms und 3000ms würfeln
        zufall_ms = random.randint(1000, 3000)
        
        # Nach dieser Zeit den eigentlichen Reiz auslösen
        QTimer.singleShot(zufall_ms, self.trigger_ausloesen)

    def trigger_ausloesen(self):
        # 5. Den eigentlichen Trigger anzeigen
        if self.visuell.isChecked():
            self.signal_frame.setStyleSheet("background-color: green;")
            print("VISUELLER REIZ!")
        else:
            # self.signal_frame.setStyleSheet("background-color: blue;")
            self.play_sound(self.sound)
            print("AKUSTISCHER REIZ!")

        # WICHTIG: Erzwinge das Neuzeichnen des Bildschirms JETZT
        QtWidgets.QApplication.processEvents()

        # 6. JETZT startet die eigentliche Datenaufnahme im Hintergrund
        dauer = self.par_dauer.value()
        frequenz = self.par_frequenz.value()
        # mess_daten = probe_funktion(dauer, frequenz)

        # time.sleep(0.10)  
        mess_daten = measurement (hat1, hat2, duration_sec=dauer, filename="Gui_Messungen/messung_probe1.csv", num_channels = 3, sampling_rate = frequenz)

        self.messung_beenden(mess_daten)
        # # 7. Nach Ablauf der Messdauer: Daten anzeigen und Frame wieder transparent
        # wartezeit_ms = int(dauer * 1000)
        # QTimer.singleShot(wartezeit_ms, lambda: self.messung_beenden(mess_daten))

    def messung_beenden(self, mess_daten):
        # Frame wieder "unsichtbar"
        self.signal_frame.setStyleSheet("background-color: transparent;")
        # wieder in den Hintergrund
        self.signal_frame.lower()

        # Plot anzeigen
        """
        mess_daten ist ein NumPy-Array mit 7 Spalten:
        [Zeit, R1, R2, R3, L1, L2, L3]
        """
        # Automatisch zum Tab mit den Graphen wechseln
        self.tabWidget.setCurrentIndex(1)

        # Vorherige Plots löschen
        self.pw_links.clear()
        self.pw_rechts.clear()

        zeit = mess_daten[:, 0]

        # --- RECHTS (Spalten 2, 3, 4 -> Indizes 1, 2, 3) ---
        # Wir plotten 3 Linien in den rechten Graphen
        self.pw_rechts.plot(zeit, mess_daten[:, 1], pen=pg.mkPen('b', width=1.5)) # Blau
        self.pw_rechts.plot(zeit, mess_daten[:, 2], pen=pg.mkPen('g', width=1.5)) # Grün
        self.pw_rechts.plot(zeit, mess_daten[:, 3], pen=pg.mkPen('y', width=1.5)) # Gelb

        # --- LINKS (Spalten 5, 6, 7 -> Indizes 4, 5, 6) ---
        # Wir plotten 3 Linien in den linken Graphen
        self.pw_links.plot(zeit, mess_daten[:, 4], pen=pg.mkPen('b', width=1.5))  # Blau
        self.pw_links.plot(zeit, mess_daten[:, 5], pen=pg.mkPen('g', width=1.5))  # Grün
        self.pw_links.plot(zeit, mess_daten[:, 6], pen=pg.mkPen('y', width=1.5))  # Gelb
        
        # Automatisch auf die Daten zoomen
        self.pw_links.autoRange()
        self.pw_rechts.autoRange()

    def play_sound(self, sound):
        # Lade die Sound-Datei
        sound.set_volume(0.1)  # 10% Lautstärke
        
        # Spiele den Sound ab
        # print("Spiele Ton ab...")
        sound.play()
        
        # Warte, bis der Ton zu Ende ist
        # time.sleep(sound.get_length())
        # print("Fertig.")
  

    def neue_messung(self):
        self.status_neue_mess.setText("Neue Messung bereit!")
        self.status_neue_mess.setStyleSheet(style_grün)
                                            
        # 2. Timer starten: Nach 2000ms (2 Sek) die Funktion 'reset_label' aufrufen
        QTimer.singleShot(2000, lambda: self.reset_label(self.status_neue_mess))

    
    def reset_label(self, name_button):
        # Den Text wieder leeren und Hintergrund entfernen
        name_button.setText("")
        name_button.setStyleSheet("background-color: transparent;")

    def daten_anzeigen(self, mess_daten):
            """
            mess_daten ist ein NumPy-Array mit 7 Spalten:
            [Zeit, R1, R2, R3, L1, L2, L3]
            """
            # Automatisch zum Tab mit den Graphen wechseln
            self.tabWidget.setCurrentIndex(1)

            # Vorherige Plots löschen
            self.pw_links.clear()
            self.pw_rechts.clear()

            zeit = mess_daten[:, 0]

            # --- RECHTS (Spalten 2, 3, 4 -> Indizes 1, 2, 3) ---
            # Wir plotten 3 Linien in den rechten Graphen
            self.pw_rechts.plot(zeit, mess_daten[:, 1], pen=pg.mkPen('b', width=1.5)) # Blau
            self.pw_rechts.plot(zeit, mess_daten[:, 2], pen=pg.mkPen('g', width=1.5)) # Grün
            self.pw_rechts.plot(zeit, mess_daten[:, 3], pen=pg.mkPen('y', width=1.5)) # Gelb

            # --- LINKS (Spalten 5, 6, 7 -> Indizes 4, 5, 6) ---
            # Wir plotten 3 Linien in den linken Graphen
            self.pw_links.plot(zeit, mess_daten[:, 4], pen=pg.mkPen('b', width=1.5))  # Blau
            self.pw_links.plot(zeit, mess_daten[:, 5], pen=pg.mkPen('g', width=1.5))  # Grün
            self.pw_links.plot(zeit, mess_daten[:, 6], pen=pg.mkPen('y', width=1.5))  # Gelb
            
            # Automatisch auf die Daten zoomen
            self.pw_links.autoRange()
            self.pw_rechts.autoRange()

    def keyPressEvent(self, event):
        """Fängt Tastendrücke ab (Not-Aus mit ESC)"""
        # In PyQt6 ist die Konstante Key_Escape
        if event.key() == Qt.Key.Key_Escape:
            print("Not-Aus: Programm wird über ESC beendet.")
            self.close()

# Standard-Startblock für PyQt6
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MeinPiProjekt()
    window.show()
    sys.exit(app.exec())