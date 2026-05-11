# import numpy as np
# import matplotlib.pyplot as plt

# def starte_daq_hardware_funktion(dauer = 4, fs = 1000):
#     """Simuliert eine 2-sekündige Messung mit 1000Hz"""
#     # fs = 1000          # Abtastrate
#     # dauer = 2          # Sekunden
#     n_samples = int(fs * dauer)
    
#     # 1. Zeitachse erstellen (0 bis 2 Sekunden)
#     zeit = np.linspace(0, dauer, n_samples)
    
#     # 2. Daten für die linke Hand (z.B. 1Hz Sinus + Rauschen)
#     links = 50 * np.sin(2 * np.pi * 1 * zeit) + np.random.normal(0, 2, n_samples)
    
#     # 3. Daten für die rechte Hand (z.B. 1.5Hz Sinus + Rauschen)
#     rechts = 40 * np.sin(2 * np.pi * 1.5 * zeit) + np.random.normal(0, 2, n_samples)
    
#     # 4. Alles in ein 2D-Array packen (Spalten: Zeit, Links, Rechts)
#     # .T transponiert es, damit wir Spalten statt Zeilen haben
#     return np.column_stack((zeit, links, rechts))


# ### probe plotten
# if __name__ == "__main__":
#     daten = starte_daq_hardware_funktion(dauer = 1, fs = 1000)

#     print (daten)
#     print (daten.shape)
#     # plt.figure(figsize=(12, 6))
#     # plt.plot(daten[:, 0], daten[:, 1], label='Links')
#     # plt.plot(daten[:, 0], daten[:, 2], label='Rechts')
#     # plt.xlabel('Zeit (s)')
#     # plt.ylabel('Amplitude')
#     # plt.title('Simulierte DAQ-Daten')
#     # plt.legend()
#     # plt.show()



import numpy as np

def probe_funktion(dauer=4, fs=1000):
    """
    Simuliert eine Messung mit 1000Hz und 7 Spalten:
    Spalte 0: Zeit
    Spalte 1-6: Verschiedene Sinus-Signale (z.B. für 6 Sensoren)
    """
    n_samples = int(fs * dauer)
    
    # 1. Zeitachse erstellen
    zeit = np.linspace(0, dauer, n_samples)
    
    # Liste für alle Spalten (Zeit ist die erste)
    spalten = [zeit]
    
    # 2. 6 verschiedene Sinus-Funktionen generieren
    # Wir variieren Frequenz (f) und Amplitude (amp) pro Spalte
    eigenschaften = [
        (1.0, 50), # Spalte 1: 1.0 Hz, 50N
        (1.2, 45), # Spalte 2: 1.2 Hz, 45N
        (0.8, 60), # Spalte 3: 0.8 Hz, 60N
        (1.5, 30), # Spalte 4: 1.5 Hz, 30N
        (0.5, 70), # Spalte 5: 0.5 Hz, 70N
        (2.0, 20)  # Spalte 6: 2.0 Hz, 20N
    ]
    
    for f, amp in eigenschaften:
        # Sinus + ein bisschen Rauschen für den Realismus
        signal = amp * np.sin(2 * np.pi * f * zeit) + np.random.normal(0, 1.5, n_samples)
        spalten.append(signal)
    
    # 3. Alle Spalten zu einem 2D-Array zusammenfügen
    return np.column_stack(spalten)

### Probe-Plotten / Test
if __name__ == "__main__":
    daten = starte_daq_hardware_funktion(dauer=2, fs=1000)
    
    print("Array Shape:", daten.shape) # Sollte (2000, 7) sein
    print("Erste Zeile:", daten[0, :])
    
    # Wenn du es kurz testen willst (Matplotlib muss installiert sein):
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 6))
    for i in range(1, 7):
        plt.plot(daten[:, 0], daten[:, i], label=f'Sensor {i}')
    plt.legend()
    plt.title("Simulation: 6 Sensor-Kanäle")
    plt.show()