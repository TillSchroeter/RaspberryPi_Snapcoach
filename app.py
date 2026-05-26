import sys
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QButtonGroup
import pyqtgraph as pg
import numpy as np
import random
import time
from daqhats import hat_list, HatIDs, mcc128, AnalogInputRange, AnalogInputMode, OptionFlags
import pygame
import RPi.GPIO as GPIO
from scipy.signal import butter, sosfiltfilt

# from daten import probe_funktion
# from main import measurement

### Boards initialisieren
board_list = hat_list(filter_by_id=HatIDs.MCC_128)
if not board_list:
    print("Kein Board gefunden!")
else:
    # Board 0 ist Links, Board 1 ist Rechts
    hat_links = mcc128(board_list[0].address)
    hat_links.a_in_mode_write(AnalogInputMode.SE)
    hat_links.a_in_range_write(AnalogInputRange.BIP_5V)

    hat_rechts = mcc128(board_list[1].address)
    hat_rechts.a_in_mode_write(AnalogInputMode.SE)
    hat_rechts.a_in_range_write(AnalogInputRange.BIP_5V)

### Initialisieren der GPIOs


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
    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def __init__(self):
        ### Initialisierung der Hauptklasse
        super().__init__()
        # Die UI-Datei laden
        uic.loadUi("app_GUI.ui", self)
        
        ### sound laden
        # Initialisiere das Sound-Modul
        pygame.mixer.init()
        self.sound = pygame.mixer.Sound("beep-01a.wav")

        ### GPIO Konfiguration für die Optokoppler 
        self.PIN_LINKS = 23         # 23 ist links (blaue)
        self.PIN_RECHTS = 24        # 24 ist rechts (orange)
        self.init_gpio()

        ### channels für messung festlegen
        self.num_channels = 6  # Anzahl der Kanäle pro Board, die gemessen werden sollen, ist fix

        ### group boxes für die radiobuttons
        # Gruppe 1: Speichern Ja/Nein
        self.gruppe_trigger = QButtonGroup(self)
        self.gruppe_trigger.addButton(self.visuell)
        self.gruppe_trigger.addButton(self.akustisch)

        # Gruppe 2: Speichern Frage
        self.gruppe_speichern = QButtonGroup(self)
        self.gruppe_speichern.addButton(self.speichern_ja)
        self.gruppe_speichern.addButton(self.speichern_nein)

        # Gruppe 3: Autozero frage
        self.gruppe_az_option = QButtonGroup(self)
        self.gruppe_az_option.addButton(self.auto_zero_ja)
        self.gruppe_az_option.addButton(self.auto_zero_nein)

        ### 1. Visuelles Feedback zurücksetzen, signal frame transparent machen und nach hinten schicken
        self.signal_frame.setStyleSheet("background-color: transparent;")
        self.signal_frame.lower()

        ### plotting vorbereiten
        # 1. Plot-Widgets erstellen
        self.pw_links_kraft = pg.PlotWidget()
        self.pw_rechts_kraft = pg.PlotWidget()
        self.pw_links_moment = pg.PlotWidget()
        self.pw_rechts_moment = pg.PlotWidget()

        # Liste für die einfachere Konfiguration in Schleifen
        self.all_plots = [
            self.pw_links_kraft, self.pw_rechts_kraft, 
            self.pw_links_moment, self.pw_rechts_moment
        ]

        # 2. Die Plot-Widgets in deine Designer-Layouts einbetten
        QtWidgets.QVBoxLayout(self.plot_links_kraft).addWidget(self.pw_links_kraft)
        QtWidgets.QVBoxLayout(self.plot_rechts_kraft).addWidget(self.pw_rechts_kraft)
        QtWidgets.QVBoxLayout(self.plot_links_moment).addWidget(self.pw_links_moment)
        QtWidgets.QVBoxLayout(self.plot_rechts_moment).addWidget(self.pw_rechts_moment)

        # 3. Gemeinsame Optik für alle Plots (Schwarze Achsen, Weißer Hintergrund)
        label_style = {'color': '#000', 'font-size': '12pt'}
        
        for pw in self.all_plots:
            pw.setBackground('w')
            # Achsen (Linien) auf Schwarz
            pw.getAxis('left').setPen('k')
            pw.getAxis('bottom').setPen('k')
            # Zahlen (Ticks) und Beschriftungen auf Schwarz setzen
            pw.getAxis('left').setTextPen('k')
            pw.getAxis('bottom').setTextPen('k')
            # Standard X-Achsen Beschriftung (Zeit ist bei allen gleich)
            pw.setLabel('bottom', 'Zeit', units='s', **label_style)
            # Legende hier EINMALIG erstellen
            pw.addLegend(offset=(10, 10), labelTextColor='k')

        # 4. Spezifische Beschriftungen und Titel
        # --- KRAFT ---
        self.pw_links_kraft.setLabel('left', 'Kraft', units='N', **label_style)
        self.pw_links_kraft.setTitle("Linke Hand - Kraft", color="k", size="12pt")
        
        self.pw_rechts_kraft.setLabel('left', 'Kraft', units='N', **label_style)
        self.pw_rechts_kraft.setTitle("Rechte Hand - Kraft", color="k", size="12pt")

        # --- MOMENT ---
        self.pw_links_moment.setLabel('left', 'Moment', units='Nm', **label_style)
        self.pw_links_moment.setTitle("Linke Hand - Moment", color="k", size="12pt")
        
        self.pw_rechts_moment.setLabel('left', 'Moment', units='Nm', **label_style)
        self.pw_rechts_moment.setTitle("Rechte Hand - Moment", color="k", size="12pt")

        # ### Monospace-Schriftart für tabellarische Textausrichtung erzwingen
        # font = QtGui.QFont("Courier New", 9)
        # self.tabelle_kraft.setFont(font)
        # self.tabelle_moment.setFont(font)

        ### Die Buttons mit Funktionen verbinden
        self.btn_start_messung.clicked.connect(self.starte_messung)
        self.btn_neue_messung.clicked.connect(self.neue_messung)
        self.btn_auto_zero.clicked.connect(self.manuelle_auto_zero_ausloesung)

        # 0 = Erster Tab, 1 = Zweiter Tab --> Steuerungs-Tab als Standard setzen
        self.tabWidget.setCurrentIndex(0)

    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def starte_messung(self):
        # altes label wenn vorhanden zurücksetzen
        self.reset_label(self.status_neue_mess)

        # #Sreenshot von der aktuellen Einstellung
        # self.screenshot_speichern("00_Vor_Messung_Einstellungen")

        ### Prüfen ob Trigger gewählt
        if not self.visuell.isChecked() and not self.akustisch.isChecked():
            self.status_mess_start.setText("Bitte Trigger wählen!")
            self.status_mess_start.setStyleSheet(style_rot)
            QTimer.singleShot(3000, lambda: self.reset_label(self.status_mess_start))
            return

        ### Prüfen ob bei messung speichern alles gewählt ist.
        # 1. Prüfen, ob überhaupt eine Speicher-Option gewählt wurde
        if not self.speichern_ja.isChecked() and not self.speichern_nein.isChecked():
            self.status_mess_start.setText("Bitte Speicher option wählen!")
            self.status_mess_start.setStyleSheet(style_rot)
            QTimer.singleShot(3000, lambda: self.reset_label(self.status_mess_start))
            return

        # 2. Wenn "Ja" gewählt ist, die ComboBoxen prüfen
        if self.speichern_ja.isChecked():
            art_wahl = self.box_art.currentText()
            nr_wahl = self.box_ver_nr.currentText()
            
            # Prüfen, ob in einer der Boxen noch der Standardtext steht
            if art_wahl == "Bitte Wählen" or nr_wahl == "Bitte Wählen":
                self.status_mess_start.setText("Bitte Art und Versuchs-Nr wählen!")
                self.status_mess_start.setStyleSheet(style_rot)
                QTimer.singleShot(3000, lambda: self.reset_label(self.status_mess_start))
                return
        ### Frage nach Auto-Zero vor der Messung prüfen
        # Prüfen ob die Option "Auto-Zero vor Start" angewählt ist
        if not self.auto_zero_ja.isChecked() and not self.auto_zero_nein.isChecked():
            self.status_mess_start.setText("Bitte Auto-Zero Option wählen!")
            self.status_mess_start.setStyleSheet(style_rot)
            QTimer.singleShot(3000, lambda: self.reset_label(self.status_mess_start))
            return

        # Wenn wir hier ankommen, sind alle Validierungen bestanden fürs Speichern
        if self.speichern_ja.isChecked():
            # Zeitstempel: JahrMonatTag_StundeMinuteSekunde (z.B. 20240520_143005)
            zeitstempel = time.strftime("%Y%m%d_%H%M%S")
            
            art_wahl = self.box_art.currentText()
            nr_wahl = self.box_ver_nr.currentText()
            
            # Dateiname nach deinem Wunsch: Art_Nr_Datum_Uhrzeit
            # Der volle Pfad für das System zum Speichern
            dateiname_nur = f"{art_wahl}_Nr{nr_wahl}_{zeitstempel}.csv"
            self.aktueller_dateiname = f"Gui_Messungen/{dateiname_nur}"
            self.soll_speichern = True
            self.speicherstatus = f"Messung als: \n{dateiname_nur}\nspeichern."
            print(f"Dateiname generiert: {self.aktueller_dateiname}")
            self.status_speichern.setStyleSheet(style_grün)
        else:
            self.aktueller_dateiname = None
            self.soll_speichern = False
            self.speicherstatus = "Messung wird nicht gespeichert (nur Angezeigt)."
            print("Messung wird nicht gespeichert (nur Angezeigt).")
            self.status_speichern.setStyleSheet(style_grau)

        # Automatisierter Auto-Zero Ablauf VOR Messungsstart
        if self.auto_zero_ja.isChecked():
            self.status_az_frage.setText("Automatischer Auto-Zero wird vor der messung ausgeführt")
            self.status_az_frage.setStyleSheet(style_grün)
            QtWidgets.QApplication.processEvents()
            self.trigger_hardware_auto_zero()
        else: 
            self.status_az_frage.setText("Kein Auto-Zero vor der Messung")
            self.status_az_frage.setStyleSheet(style_grau)

        #Variablen
        vorbereitung = 2000 #ms

        # Vorbereitung: Status setzen für messung starten
        self.status_mess_start.setText("Bereit machen...")
        self.status_mess_start.setStyleSheet(style_grau)
        # Status setzen für Speicherung
        self.status_speichern.setText(self.speicherstatus)
        
        # #Sreenshot von der aktuellen Einstellung
        # self.screenshot_speichern("00_Vor_Messung_Mit_Einstellungen")

        # Timer starten: die Funktion 'reset_label' aufrufen
        QTimer.singleShot(vorbereitung, lambda: self.reset_label(self.status_mess_start))
        QTimer.singleShot(vorbereitung, lambda: self.reset_label(self.status_speichern))
        QTimer.singleShot(vorbereitung, lambda: self.reset_label(self.status_auto_zero))
        QTimer.singleShot(vorbereitung, lambda: self.reset_label(self.status_az_frage))


        # Hebt den Frame über alle anderen Elemente
        # self.signal_frame.raise_()

        ### Kette starten: wird das Bild WEISS (Vorbereitung für Athlet)
        QTimer.singleShot(vorbereitung, self.trigger_vorbereitung)
    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def trigger_vorbereitung(self):
        # Frame nach ganz vorne holen und anzeigen
        self.signal_frame.raise_()
        self.signal_frame.show()
        # Weiß machen
        self.signal_frame.setStyleSheet("background-color: white; border: none;")
        
        # # WICHTIG: Qt anweisen, das Weiß-Werden sofort auf dem Display zu rendern
        # QtWidgets.QApplication.processEvents()
        
        # # NEU: Screenshot vom weißen Zustand speichern
        # self.screenshot_speichern("01_Bereit_Weiss")

        # 4. Zufallszeit zwischen 1500ms und 3500ms würfeln
        zufall_ms = random.randint(1500, 3500)
        
        # Nach dieser Zeit den eigentlichen Reiz auslösen
        QTimer.singleShot(zufall_ms, self.trigger_ausloesen)
    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def trigger_ausloesen(self):
        # Sicherheitshalber nochmal nach vorne holen
        self.signal_frame.raise_()

        # Den eigentlichen Trigger anzeigen
        if self.visuell.isChecked():
            self.signal_frame.setStyleSheet("background-color: green;")
            print("VISUELLER REIZ!")
            # # WICHTIG: Erzwinge das Neuzeichnen (Grün-Werden) JETZT vor dem Screenshot
            # QtWidgets.QApplication.processEvents()
            
            # # NEU: Screenshot vom grünen Zustand speichern
            # self.screenshot_speichern("02_Reiz_Gruen")
        else:
            # self.signal_frame.setStyleSheet("background-color: blue;")
            self.play_sound(self.sound)
            print("AKUSTISCHER REIZ!")

        # WICHTIG: Erzwinge das Neuzeichnen des Bildschirms JETZT
        QtWidgets.QApplication.processEvents()

        ### JETZT startet die eigentliche Datenaufnahme im Hintergrund
        dauer = self.par_dauer.value()
        frequenz = self.par_frequenz.value()

        ### Hier rufen wir die Messfunktion auf, die die Daten von den Boards abholt
        mess_daten, frames_written = self.measurement (hat_links, hat_rechts, duration_sec = dauer, num_channels = self.num_channels, sampling_rate = frequenz)
        # Rohwerte in physikalische Einheiten umrechnen
        mess_daten_phys = self.werte_verarbeiten(mess_daten)

        # wenn gespeichert werden soll, dann hier tun
        if self.soll_speichern:
            self.speichern_csv(self.aktueller_dateiname, mess_daten_phys, frames_written)

        # messung beenden (Plot anzeigen und Frame zurücksetzen)
        self.messung_beenden(mess_daten_phys)
        # # 7. Nach Ablauf der Messdauer: Daten anzeigen und Frame wieder transparent
        # wartezeit_ms = int(dauer * 1000)
        # QTimer.singleShot(wartezeit_ms, lambda: self.messung_beenden(mess_daten))

    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def measurement(self, hat_links, hat_rechts, duration_sec, num_channels = 6, sampling_rate = 1000.0):
        # sampling_rate = 1000.0
        # num_channels = 6
        # channel_mask = (0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F, 0x7F, 0xFF)     # Maske für alle acht Kanäle (immer von channel 0 bis channel num_channels - 1)
        # 0x77 maske für 0,1,2  4,5,6        
        total_frames = int(round(duration_sec * sampling_rate))             # round um kleine latenzen aus der GUI auszugleichen
        frames_written = 0
        # Wir speichern als float64 
        all_data = np.zeros((total_frames, 1 + 2 * num_channels), dtype=np.float64)


        print(f"Messung wird gestartet: {num_channels} Kanäle bei zwei Boards und {duration_sec}s...")


        hat_links.a_in_scan_start(channel_mask = 0x77,
                            samples_per_channel=0, 
                            sample_rate_per_channel=sampling_rate, 
                            options=OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA)

        hat_rechts.a_in_scan_start(channel_mask = 0x77,
                            samples_per_channel=0,
                            sample_rate_per_channel=sampling_rate, 
                            options=OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA | OptionFlags.EXTCLOCK) # externe Clock


        samples_per_block = 100
        frames_written = 0
        try:
            while frames_written < total_frames:
                # 1. Daten abholen (wartet bis zu 0.1s auf die 100 Samples)
                result1 = hat_links.a_in_scan_read(samples_per_channel=samples_per_block, timeout=0.1)
                result2 = hat_rechts.a_in_scan_read(samples_per_channel=samples_per_block, timeout=0.1)
                # print ("hier in der Schleife")

                # 2. Prüfen, wie viele Zeilen wir WIRKLICH bekommen haben
                # (Das löst den ValueError, da wir nicht mehr von festen 100 ausgehen)
                actual_count1 = len(result1.data) // num_channels
                actual_count2 = len(result2.data) // num_channels
                
                # Wir nehmen das Minimum von beiden, um synchron zu bleiben
                actual_count = min(actual_count1, actual_count2)

                if actual_count > 0:
                    # print ("hier im if actual_count > 0")
                    # Nur so viele Daten nehmen, wie wir auch wirklich brauchen (total_frames beachten)
                    if frames_written + actual_count > total_frames:
                        actual_count = total_frames - frames_written

                    # 3. Daten in die richtige Form bringen
                    # Hier nutzen wir jetzt actual_count statt der festen 100
                    block1 = np.array(result1.data[:actual_count * num_channels], dtype=np.float64).reshape(actual_count, num_channels)
                    block2 = np.array(result2.data[:actual_count * num_channels], dtype=np.float64).reshape(actual_count, num_channels)
                    
                    # 4. Zeitstempel für diesen Block berechnen
                    t_start = (frames_written + 1) / sampling_rate
                    t_end = (frames_written + actual_count) / sampling_rate
                    t_block = np.linspace(t_start, t_end, actual_count)

                    # 5. In das Haupt-Array einfügen
                    idx_end = frames_written + actual_count
                    all_data[frames_written:idx_end, 0] = t_block
                    all_data[frames_written:idx_end, 1:1+num_channels] = block1
                    all_data[frames_written:idx_end, 1+num_channels:] = block2

                    frames_written += actual_count
                
                
                # um die Gui nicht zu blockieren
                QtWidgets.QApplication.processEvents()                
                # Kleines Sleep zur CPU-Schonung
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("Abbruch!")

        # Cleanup
        hat_links.a_in_scan_stop()
        hat_rechts.a_in_scan_stop()
        hat_links.a_in_scan_cleanup()
        hat_rechts.a_in_scan_cleanup()

        return all_data, frames_written
    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def speichern_csv(self, dateiname, data_phys, frames_written):
        """
        Speichert das verarbeitete (kalibrierte) Array als CSV mit einem 
        dreizeiligen Metadaten-Header (Parameter, Werte, Spaltennamen).
        """
        print(f"Speichere {frames_written} Zeilen in {dateiname}...")

        # =========================================================================
        # 1. METADATEN DYNAMISCH AUS DER GUI/KLASSE HOLEN
        # =========================================================================
        # Falls deine Variablen anders heißen, hier die Namen kurz anpassen:
        messart = self.box_art.currentText() if hasattr(self, 'box_art') else "Unbekannt"
        versuchsnummer = self.box_ver_nr.currentText() if hasattr(self, 'box_ver_nr') else "Unbekannt"
        dauer = self.par_dauer.value() if hasattr(self, 'par_dauer') else "Unbekannt"
        sampling_frequenz = self.par_frequenz.value() if hasattr(self, 'par_frequenz') else "Unbekannt"

        
        # Trigger-Art über die RadioButtons ermitteln (.isChecked())
        if self.visuell.isChecked():
            trigger_art = "Visueller Reiz"
        elif self.akustisch.isChecked():
            trigger_art = "Akustischer Reiz"
        else:
            trigger_art = "Unbekannt"

        # Überprüfen ob automatischer Auto-Zero vor der Messung gewählt wurde
        if self.auto_zero_ja.isChecked():
            auto_zero_status = "Ja"
        elif self.auto_zero_nein.isChecked():
            auto_zero_status = "Nein"
        else:
            auto_zero_status = "Unbekannt"
        # =========================================================================
        # 2. DREIZEILIGEN HEADER BAUEN
        # =========================================================================
        # Zeile 1: Die Bezeichnungen der Metadaten-Spalten
        meta_names = "Messart,Versuchsnummer,Dauer,Sampling-Frequenz,Trigger-Art,Auto-Zero vor Messung"
        
        # Zeile 2: Die echten Werte (durch Komma getrennt)
        meta_values = f"{messart},{versuchsnummer},{dauer},{sampling_frequenz},{trigger_art},{auto_zero_status}"
        
        # Zeile 3: Die Spaltennamen für deine 13 Daten-Kanäle
        header_list = [
            "Time", 
            "L_Fx", "L_Fy", "L_Fz", "L_Mx", "L_My", "L_Mz",
            "R_Fx", "R_Fy", "R_Fz", "R_Mx", "R_My", "R_Mz"
        ]
        data_columns = ",".join(header_list)

        # Zusammenfügen der drei Zeilen (getrennt durch Zeilenumbrüche \n)
        # NumPy setzt standardmäßig ein '#' vor den Header. Mit comments='' unterdrücken wir das,
        # damit die Datei sofort rein als CSV gelesen werden kann.
        kompletter_header = f"{meta_names}\n{meta_values}\n{data_columns}"

        # =========================================================================
        # 3. FORMATIERUNG UND SPEICHERN
        # =========================================================================
        # '%.4f' für die Zeit, '%.2f' für alle nachfolgenden Kräfte und Momente
        fmt = ['%.4f'] + ['%.2f'] * (data_phys.shape[1] - 1)
        
        try:
            # Wir speichern nur die tatsächlich geschriebenen Zeilen (frames_written)
            np.savetxt(
                dateiname, 
                data_phys[:frames_written, :], 
                delimiter=",", 
                header=kompletter_header, 
                comments='', 
                fmt=fmt
            )
            print("CSV-Datei inklusive strukturiertem Metadaten-Header erfolgreich gespeichert!")
        except Exception as e:
            print(f"Fehler beim Speichern der CSV: {e}")
    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def werte_verarbeiten(self, all_data):
        """
        Verarbeitet Roh-ADC-Werte in physikalische Einheiten (N und Nm)
        und filtert die mechanischen Eigenfrequenzen der KMP heraus.
        all_data Aufbau:
        [0]: Zeit
        [1-3]: Fx, Fy, Fz (Board 1 - Links)
        [4-6]: Mx, My, Mz (Board 1 - Links)
        [7-9]: Fx, Fy, Fz (Board 2 - Rechts)
        [10-12]: Mx, My, Mz (Board 2 - Rechts)
        """
        # 1. Kopie erstellen
        data_phys = np.copy(all_data).astype(np.float64)
        
        # 2. Baseline-Korrektur (Tara)
        # Wir berechnen den Nullpunkt-Offset aus den ersten 10 Zeilen der Messung
        # (Voraussetzung: Proband übt zu Beginn noch keine Kraft aus)
        # offset = np.mean(data_phys[:10, 1:], axis=0)
        # data_phys[:, 1:] -= offset
        

        # 3. Definition der Skalierungsfaktoren (MaxLoad / 32768)
        f_fx_fy = 5000.0 / 32768.0      # Fx und Fy haben den faktor 5000 N bei voller Auslenkung
        f_fz    = 10000.0 / 32768.0     # Fz hat den faktor 10000 N bei voller Auslenkung
        f_mx    = 3000.0 / 32768.0      # Mx hat den faktor 3000 Nm bei voller Auslenkung
        f_my    = 2000.0 / 32768.0      # My hat den faktor 2000 Nm bei voller Auslenkung
        f_mz    = 1500.0 / 32768.0       # Mz hat den faktor 1500 Nm bei voller Auslenkung

        # für alle daten einmal die Mitte des Messbereiches vom ADC rohwert abziehen
        # Formel: Kraft (N) = (ADC_Rohwert - 32768) * (Maximalbereich(N) / 32768)
        data_phys[:, 1:] -= 32768.0
        # 4. Faktoren auf Board 1 (Links) anwenden
        data_phys[:, 1] *= f_fx_fy  # CH0: Fx
        data_phys[:, 2] *= f_fx_fy  # CH1: Fy
        data_phys[:, 3] *= f_fz     # CH2: Fz
        data_phys[:, 4] *= f_mx     # CH3: Mx
        data_phys[:, 5] *= f_my     # CH4: My
        data_phys[:, 6] *= f_mz     # CH5: Mz

        # 5. Faktoren auf Board 2 (Rechts) anwenden
        data_phys[:, 7] *= f_fx_fy  # CH0: Fx
        data_phys[:, 8] *= f_fx_fy  # CH1: Fy
        data_phys[:, 9] *= f_fz     # CH2: Fz
        data_phys[:, 10] *= f_mx    # CH3: Mx
        data_phys[:, 11] *= f_my    # CH4: My
        data_phys[:, 12] *= f_mz    # CH5: Mz

        # =========================================================================
        # 6. DIGITALER TIEFPASSFILTER (BUTTERWORTH 4. ORDNUNG)
        # =========================================================================
        fs = 1000.0       # Deine Abtastrate (1000 Hz laut Systemauslegung)
        fc = 90.0         # Grenzfrequenz (90 Hz: idealer Kompromiss unterhalb der 110 Hz Eigenfrequenz)
        order = 4         # Filterordnung für eine steile Trennung

        # Überprüfen, ob das Array genügend Zeilen/Datenpunkte zum Filtern besitzt
        # (sosfiltfilt benötigt eine minimale Mindestanzahl an Samples)
        if data_phys.shape[0] > 30:
            # Filterkoeffizienten als Second-Order Sections (SOS) berechnen (sehr stabil)
            sos = butter(order, fc, btype='low', fs=fs, output='sos')
            
            # Filter auf alle Signalspalten (Index 1 bis 12) anwenden
            # Spalte 0 ist der Zeitvektor und darf NIEMALS gefiltert werden!
            for col in range(1, 13):
                # sosfiltfilt filtert vorwärts + rückwärts -> Verhindert Phasenverschiebung!
                data_phys[:, col] = sosfiltfilt(sos, data_phys[:, col])

        return data_phys

    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def messung_beenden(self, processed_data):
            """
            processed_data Aufbau:
            [0]: Zeit
            [1-3]: L_Fx, L_Fy, L_Fz | [4-6]: L_Mx, L_My, L_Mz
            [7-9]: R_Fx, R_Fy, R_Fz | [10-12]: R_Mx, R_My, R_Mz
            """
            # --- TRIGGERART IM LABEL ANZEIGEN ---
            if self.visuell.isChecked():
                self.par_bedingung.setText("Visueller Reiz")
                self.par_bedingung.setStyleSheet(style_grün)
            else:
                self.par_bedingung.setText("Akustischer Reiz")
                self.par_bedingung.setStyleSheet(style_grün)

            # 1. Visuelles Feedback zurücksetzen
            self.signal_frame.setStyleSheet("background-color: transparent;")
            self.signal_frame.lower()

            # 2. Zum Tab-Widget für die Graphen wechseln (Plotting-Tab)
            self.tabWidget.setCurrentIndex(1) 

            # Vorherige Plots löschen - Die Legende bleibt durch das clear() 
            # erhalten, wird aber geleert und beim Plotten neu befüllt.
            self.pw_links_kraft.clear()
            self.pw_rechts_kraft.clear()
            self.pw_links_moment.clear()
            self.pw_rechts_moment.clear()

            zeit = processed_data[:, 0]

            # --- MATPLOTLIB FARBEN & STIL ---
            # Breite 2.0 ist deutlich besser sichtbar auf dem 7" Screen
            pen_x = pg.mkPen(color='#1f77b4', width=2) # Blau
            pen_y = pg.mkPen(color='#ff7f0e', width=2) # Orange
            pen_z = pg.mkPen(color='#2ca02c', width=2) # Grün

            # --- LINKS PLOTTEN ---
            # Kraft
            self.pw_links_kraft.plot(zeit, processed_data[:, 1], pen=pen_x, name="Fx")
            self.pw_links_kraft.plot(zeit, processed_data[:, 2], pen=pen_y, name="Fy")
            self.pw_links_kraft.plot(zeit, processed_data[:, 3], pen=pen_z, name="Fz")
            
            # Momente
            self.pw_links_moment.plot(zeit, processed_data[:, 4], pen=pen_x, name="Mx")
            self.pw_links_moment.plot(zeit, processed_data[:, 5], pen=pen_y, name="My")
            self.pw_links_moment.plot(zeit, processed_data[:, 6], pen=pen_z, name="Mz")

            # --- RECHTS PLOTTEN ---
            # Kraft
            self.pw_rechts_kraft.plot(zeit, processed_data[:, 7], pen=pen_x, name="Fx")
            self.pw_rechts_kraft.plot(zeit, processed_data[:, 8], pen=pen_y, name="Fy")
            self.pw_rechts_kraft.plot(zeit, processed_data[:, 9], pen=pen_z, name="Fz")
            
            # Momente
            self.pw_rechts_moment.plot(zeit, processed_data[:, 10], pen=pen_x, name="Mx")
            self.pw_rechts_moment.plot(zeit, processed_data[:, 11], pen=pen_y, name="My")
            self.pw_rechts_moment.plot(zeit, processed_data[:, 12], pen=pen_z, name="Mz")

            # 3. Zoom anpassen
            for pw in [self.pw_links_kraft, self.pw_rechts_kraft, self.pw_links_moment, self.pw_rechts_moment]:
                pw.autoRange()
            
            ######### Parameter für die Tabellen #########
            ### --- KRAFT-TABELLE BEFÜLLEN ---
            # Links Kraft
            l_fx_max, l_fx_min = np.max(processed_data[:, 1]), np.min(processed_data[:, 1])
            l_fy_max, l_fy_min = np.max(processed_data[:, 2]), np.min(processed_data[:, 2])
            l_fz_max = np.max(processed_data[:, 3])

            self.tabelle_kraft.setItem(1, 0, QtWidgets.QTableWidgetItem(f"Max.: {l_fx_max:.1f}     Min.: {l_fx_min:.1f}"))
            self.tabelle_kraft.setItem(1, 1, QtWidgets.QTableWidgetItem(f"Max.: {l_fy_max:.1f}     Min.: {l_fy_min:.1f}"))
            self.tabelle_kraft.setItem(1, 2, QtWidgets.QTableWidgetItem(f"Max.: {l_fz_max:.1f}"))

            # Rechts Kraft
            r_fx_max, r_fx_min = np.max(processed_data[:, 7]), np.min(processed_data[:, 7])
            r_fy_max, r_fy_min = np.max(processed_data[:, 8]), np.min(processed_data[:, 8])
            r_fz_max = np.max(processed_data[:, 9])

            self.tabelle_kraft.setItem(2, 0, QtWidgets.QTableWidgetItem(f"Max.: {r_fx_max:.1f}     Min.: {r_fx_min:.1f}"))
            self.tabelle_kraft.setItem(2, 1, QtWidgets.QTableWidgetItem(f"Max.: {r_fy_max:.1f}     Min.: {r_fy_min:.1f}"))
            self.tabelle_kraft.setItem(2, 2, QtWidgets.QTableWidgetItem(f"Max.: {r_fz_max:.1f}"))

            ### --- MOMENTEN-TABELLE BEFÜLLEN ---
            # Links Momente
            l_mx_max, l_mx_min = np.max(processed_data[:, 4]), np.min(processed_data[:, 4])
            l_my_max, l_my_min = np.max(processed_data[:, 5]), np.min(processed_data[:, 5])
            l_mz_max, l_mz_min = np.max(processed_data[:, 6]), np.min(processed_data[:, 6])

            self.tabelle_moment.setItem(1, 0, QtWidgets.QTableWidgetItem(f"Max.: {l_mx_max:.1f}     Min.: {l_mx_min:.1f}"))
            self.tabelle_moment.setItem(1, 1, QtWidgets.QTableWidgetItem(f"Max.: {l_my_max:.1f}     Min.: {l_my_min:.1f}"))
            self.tabelle_moment.setItem(1, 2, QtWidgets.QTableWidgetItem(f"Max.: {l_mz_max:.1f}     Min.: {l_mz_min:.1f}"))

            # Rechts Momente
            r_mx_max, r_mx_min = np.max(processed_data[:, 10]), np.min(processed_data[:, 10])
            r_my_max, r_my_min = np.max(processed_data[:, 11]), np.min(processed_data[:, 11])
            r_mz_max, r_mz_min = np.max(processed_data[:, 12]), np.min(processed_data[:, 12])

            self.tabelle_moment.setItem(2, 0, QtWidgets.QTableWidgetItem(f"Max.: {r_mx_max:.1f}     Min.: {r_mx_min:.1f}"))
            self.tabelle_moment.setItem(2, 1, QtWidgets.QTableWidgetItem(f"Max.: {r_my_max:.1f}     Min.: {r_my_min:.1f}"))
            self.tabelle_moment.setItem(2, 2, QtWidgets.QTableWidgetItem(f"Max.: {r_mz_max:.1f}     Min.: {r_mz_min:.1f}"))

            ### Reaktionzeiten
            # --- REAKTIONSZEIT-BERECHNUNG (Schwelle: Fz > 15N) ---
            zeit_vektor = processed_data[:, 0]
            l_fz = processed_data[:, 3]  # Index 3 = L_Fz
            r_fz = processed_data[:, 9]  # Index 9 = R_Fz

            # Indizes finden, wo Fz > 15 N ist
            idx_links = np.where(l_fz > 15.0)[0]
            idx_rechts = np.where(r_fz > 15.0)[0]

            # Reaktionszeit Links bestimmen
            if len(idx_links) > 0:
                reaktion_links = zeit_vektor[idx_links[0]]
                text_links = f"{reaktion_links:.3f} s"
            else:
                reaktion_links = None
                text_links = "Kein Wert"

            # Reaktionszeit Rechts bestimmen
            if len(idx_rechts) > 0:
                reaktion_rechts = zeit_vektor[idx_rechts[0]]
                text_rechts = f"{reaktion_rechts:.3f} s"
            else:
                reaktion_rechts = None
                text_rechts = "Kein Wert"

            # --- TABELLE: tabelle_reaktion_li_re BEFÜLLEN ---
            # Tabelle hat 1 Zeile (Index 0) und 2 Spalten: Spalte 0 = Links, Spalte 1 = Rechts
            self.tabelle_reaktion_li_re.setItem(0, 0, QtWidgets.QTableWidgetItem(text_links))
            self.tabelle_reaktion_li_re.setItem(1, 0, QtWidgets.QTableWidgetItem(text_rechts))

            # --- DURCHSCHNITT UND DIFFERENZ BERECHNEN ---
            if reaktion_links is not None and reaktion_rechts is not None:
                durchschnitt = (reaktion_links + reaktion_rechts) / 2.0
                differenz = abs(reaktion_links - reaktion_rechts)
                text_durchschnitt = f"{durchschnitt:.3f} s"
                text_differenz = f"{differenz:.3f} s"
            else:
                text_durchschnitt = "N/A"
                text_differenz = "N/A"

            # --- TABELLE: tabelle_reaktion_durchschnitt BEFÜLLEN ---
            # Bereinigte Adressierung ohne redundante, fehlerhafte Doppelaufrufe
            self.tabelle_reaktion_durchschnitt.setItem(0, 0, QtWidgets.QTableWidgetItem(text_durchschnitt))
            self.tabelle_reaktion_durchschnitt.setItem(1, 0, QtWidgets.QTableWidgetItem(text_differenz))


            # UI für Änderungen sperren, bis "Neue Messung" gedrückt wird
            self.set_ui_enabled(False)
            # altes label wenn vorhanden zurücksetzen
            self.reset_label(self.status_neue_mess)
            # # Fokus auf den "Neue Messung" Button lenken
            # self.btn_neue_messung.setFocus()
        
    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def play_sound(self, sound):
        # Lade die Sound-Datei
        sound.set_volume(0.5)  # 10% Lautstärke
        
        # Spiele den Sound ab
        # print("Spiele Ton ab...")
        sound.play()
        
        # Warte, bis der Ton zu Ende ist
        # time.sleep(sound.get_length())
        # print("Fertig.")
  
    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""

    def neue_messung(self):
        # 1. Speicherstatus prüfen & Nummer nur bei Erfolg hochzählen
        wurde_gespeichert = hasattr(self, 'soll_speichern') and self.soll_speichern
        
        if wurde_gespeichert and self.aktueller_dateiname:
            datei_kurz = self.aktueller_dateiname.split('/')[-1]
            status_text = f"letze Messung gespeichert:\n{datei_kurz}\nBereit für neue Messung!"
            
            # NUR JETZT die Nummer hochsetzen
            aktuelle_nr_index = self.box_ver_nr.currentIndex()
            if aktuelle_nr_index < self.box_ver_nr.count() - 1:
                self.box_ver_nr.setCurrentIndex(aktuelle_nr_index + 1)
        else:
            status_text = "Letzte Messung nicht gespeichert.\nBereit für neue Messung!"

        # 2. UI wieder freigeben
        self.set_ui_enabled(True)

        # 3. RadioButtons wirklich abwählen (über die ButtonGroups)
        self.gruppe_speichern.setExclusive(False)
        self.gruppe_trigger.setExclusive(False)
        self.gruppe_az_option.setExclusive(False)
        
        self.speichern_ja.setChecked(False)
        self.speichern_nein.setChecked(False)
        self.visuell.setChecked(False)
        self.akustisch.setChecked(False)
        self.auto_zero_ja.setChecked(False)
        self.auto_zero_nein.setChecked(False)
        
        self.gruppe_speichern.setExclusive(True)
        self.gruppe_trigger.setExclusive(True)
        self.gruppe_az_option.setExclusive(True)

        # 4. Restliches Feedback
        self.status_neue_mess.setText(status_text)
        self.status_neue_mess.setStyleSheet(style_grün)
        for pw in self.all_plots:
            pw.clear()
        
        # Tabellen-Inhalte leeren (ohne die Header zu löschen)
        tabellen_liste = [
            self.tabelle_kraft, 
            self.tabelle_moment, 
            self.tabelle_reaktion_li_re, 
            self.tabelle_reaktion_durchschnitt
        ]
        # Tabellen-Inhalte struktursicher leeren
        # 1. Kraft- und Momententabelle: Erst ab Zeile 1 (Index 1) leeren, um Header-Texte zu schützen
        for tabelle in [self.tabelle_kraft, self.tabelle_moment]:
            for row in range(1, tabelle.rowCount()):  # Startet bei 1 statt 0
                for col in range(tabelle.columnCount()):
                    tabelle.setItem(row, col, QtWidgets.QTableWidgetItem(""))

        # 2. Reaktionstabellen: Komplett ab Zeile 0 (Index 0) leeren
        for tabelle in [self.tabelle_reaktion_li_re, self.tabelle_reaktion_durchschnitt]:
            for row in range(tabelle.rowCount()):      # Startet komplett bei 0
                for col in range(tabelle.columnCount()):
                    tabelle.setItem(row, col, QtWidgets.QTableWidgetItem(""))
        
        # altes label wenn vorhanden zurücksetzen
        self.reset_label(self.par_bedingung)
        
        # QTimer.singleShot(4000, lambda: self.reset_label(self.status_neue_mess))
    
    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def set_ui_enabled(self, state):
        """Aktiviert oder deaktiviert alle Eingaben auf dem Steuerungs-Tab"""
        # Liste aller Widgets, die gesperrt werden sollen
        widgets = [
            self.speichern_ja, self.speichern_nein, 
            self.visuell, self.akustisch,
            self.box_art, self.box_ver_nr, 
            self.par_dauer, self.par_frequenz,
            self.btn_start_messung,
            self.auto_zero_ja, self.auto_zero_nein,
            self.btn_auto_zero
        ]
        for w in widgets:
            w.setEnabled(state)

    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def reset_label(self, name_button):
        # Den Text wieder leeren und Hintergrund entfernen
        name_button.setText("")
        name_button.setStyleSheet("background-color: transparent;")

    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def init_gpio(self):
        """Initialisiert die Hardware-Pins für die Optokoppler"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PIN_LINKS, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.PIN_RECHTS, GPIO.OUT, initial=GPIO.LOW)

    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def trigger_hardware_auto_zero(self):
        """Erzeugt den benötigten High-Puls an den Optokopplern"""
        GPIO.output(self.PIN_LINKS, GPIO.HIGH)
        GPIO.output(self.PIN_RECHTS, GPIO.HIGH)
        time.sleep(0.1)  # 100ms Schaltimpuls
        GPIO.output(self.PIN_LINKS, GPIO.LOW)
        GPIO.output(self.PIN_RECHTS, GPIO.LOW)
        time.sleep(0.2)  # Einschwingzeit für KMP-Verstärker

    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def manuelle_auto_zero_ausloesung(self):
        """Führt Auto-Zero über den direkten GUI-Button aus"""
        self.status_auto_zero.setText("Auto-Zero wird ausgeführt...")
        self.status_auto_zero.setStyleSheet(style_grau)
        QtWidgets.QApplication.processEvents()
        
        self.trigger_hardware_auto_zero()
        
        self.status_auto_zero.setText("Hardware Auto-Zero abgeschlossen!")
        self.status_auto_zero.setStyleSheet(style_grün)
        QTimer.singleShot(3000, lambda: self.reset_label(self.status_auto_zero))
    """--------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    def screenshot_speichern(self, dateiname_zusatz):
        """Erstellt einen Screenshot des gesamten Fensters und speichert ihn ab"""
        # Ordner definieren (analog zu Ihren Messdaten)
        import os
        os.makedirs("GUI_Screenshots", exist_ok=True)
        
        # Zeitstempel für den Dateinamen generieren
        zeit = time.strftime("%Y%m%d_%H%M%S")
        filepath = f"GUI_Screenshots/Screenshot_{dateiname_zusatz}_{zeit}.png"
        
        # Das gesamte Hauptfenster als Bild erfassen
        screen = self.grab()
        
        # Speichern
        if screen.save(filepath, "PNG"):
            print(f"Screenshot erfolgreich gespeichert: {filepath}")
        else:
            print("Fehler beim Speichern des Screenshots.")

    def keyPressEvent(self, event):
        """Fängt Tastendrücke ab (Not-Aus mit ESC)"""
        # In PyQt6 ist die Konstante Key_Escape
        if event.key() == Qt.Key.Key_Escape:
            print("Not-Aus: Programm wird über ESC beendet.")
            GPIO.cleanup()
            self.close()
    def closeEvent(self, event):
        """Bereinigt die GPIOs beim regulären Schließen des Fensters"""
        GPIO.cleanup()
        event.accept()

# Standard-Startblock für PyQt6
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MeinPiProjekt()
    window.show()
    sys.exit(app.exec())