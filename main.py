from daqhats import OptionFlags, hat_list, HatIDs, mcc128, AnalogInputRange
import time
import numpy as np
import csv

### Boards auflisten
board_list = hat_list(filter_by_id=HatIDs.MCC_128)

# checken, ob Boards gefunden wurden
if board_list:
    print(f"Gefundene Boards: {len(board_list)}")

    for entry in board_list:
        print(f"Board gefunden an Adresse: {entry.address}")
else:
    print("Keine MCC 128 Boards gefunden. Jumper checken!")


### Boards initialisieren
hat1 = mcc128(board_list[0].address)

### Spannungsbereich auf +/- 5V setzen
hat1.a_in_range_write(AnalogInputRange.BIP_5V)

# ### Scan bauen
# # Die Maske 0x3F würde bedeuten: Kanäle 0, 1, 2, 3, 4, 5 sind aktiv (1+2+4+8+16+32 = 63 = 0x3F) hier jetz nur einen kanal aktivieren: 0x01

# channel_mask = 0x01 
# samples_per_channel = 0     # 0 für kontinuierlichen Betrieb
# sample_rate = 1000          # 1000 Hz pro Kanal
# options = OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA

# # Scan starten
# hat1.a_in_scan_start(channel_mask, samples_per_channel, sample_rate, options)


def measurement(hat, duration_sec, filename):
    sampling_rate = 1000.0  # Hz
    total_samples = int(duration_sec * sampling_rate)
    
    # Scan starten (Kanal 0)
    hat.a_in_scan_start(channel_mask=0x01, samples_per_channel=0, 
                        sample_rate_per_channel=sampling_rate, 
                        options=OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA)
    
    print(f"Messung läuft für {duration_sec} Sekunden ({total_samples} Samples)...")
    
    samples_read = 0
    
    with open(filename, mode='w', newline='') as file: # 'w' überschreibt die Datei
        writer = csv.writer(file)
        writer.writerow(["time", "value"]) # Kopfzeile
        
        try:
            while samples_read < total_samples:
                # Wir lesen kleine Blöcke aus dem Puffer
                result = hat.a_in_scan_read(samples_per_channel=-1, timeout=0.1)
                
                if result.buffer_overrun:
                    print("FEHLER: Buffer voll!")
                    break
                
                if len(result.data) > 0:
                    for value in result.data:
                        # Berechne Zeit basierend auf Counter
                        time_val = samples_read / sampling_rate
                        writer.writerow([f"{time_val:.3f}", value])
                        samples_read += 1
                        
                        # Abbruch, falls Ziel erreicht
                        if samples_read >= total_samples:
                            break
                
                time.sleep(0.01) # Kurzes Sleep für die CPU
              
        except KeyboardInterrupt:
            print("Messung vorzeitig abgebrochen.")

    # Aufräumen
    hat.a_in_scan_stop()        # Scan stoppen
    hat.a_in_scan_cleanup()     # Ressourcen freigeben

    print(f"Messung beendet. Daten gespeichert in {filename}")

    

### Aufruf der Funktion (Beispiel: 10 Sekunden)
measurement(hat1, 4, "Messungen/messung_probe.csv")



