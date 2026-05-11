import time
import csv
import numpy as np
from daqhats import hat_list, HatIDs, mcc128, AnalogInputRange, AnalogInputMode, OptionFlags

def measurement(hat1, hat2, duration_sec, filename, num_channels = 3, sampling_rate = 1000.0):
    # sampling_rate = 1000.0
    # num_channels = 3
    channel_mask = (0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F, 0x7F, 0xFF)  # Maske für alle acht Kanäle
    total_frames = int(duration_sec * sampling_rate)
    frames_written = 0
    # Wir speichern die Zeit als float64 und die ADC-Werte als int32
    all_data = np.zeros((total_frames, 1 + 2 * num_channels), dtype=object)


    print(f"Messung wird gestartet: {num_channels} Kanäle bei zwei Boards und {duration_sec}s...")

    hat1.a_in_scan_start(channel_mask = channel_mask[num_channels-1], samples_per_channel=0, 
                        sample_rate_per_channel=sampling_rate, 
                        options=OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA)

    hat2.a_in_scan_start(channel_mask = channel_mask[num_channels-1], samples_per_channel=0,
                        sample_rate_per_channel=sampling_rate, 
                        options=OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA)
    #samples_per_channel=0 bedeutet hier: Messe unendlich lange weiter, bis ich "Stopp" sage.

    frames_written = 0
    try:
        while frames_written < total_frames:
            # Lese einen vollen Datensatz (1 sample pro kanal * num_channels)
            result1 = hat1.a_in_scan_read(samples_per_channel=1, timeout=0.1)
            result2 = hat2.a_in_scan_read(samples_per_channel=1, timeout=0.1)
            
            if len(result1.data) == num_channels and len(result2.data) == num_channels:
                # Zeitstempel berechnen
                t = (frames_written + 1) / sampling_rate
                
                # In unser Array schreiben
                all_data[frames_written, 0] = t
                all_data[frames_written, 1:1+num_channels] = result1.data
                all_data[frames_written, 1+num_channels:] = result2.data
                
                frames_written += 1
            
            # Kein sleep() nötig, wenn wir so schnell wie möglich sammeln wollen, 
            # aber ein minimaler sleep schont die CPU für andere Prozesse
            # time.sleep(0.001)

    except KeyboardInterrupt:
        print("Abbruch!")

    # Cleanup
    hat1.a_in_scan_stop()
    hat2.a_in_scan_stop()
    hat1.a_in_scan_cleanup()
    hat2.a_in_scan_cleanup()

    # Jetzt erst alles in die CSV schreiben
    print(f"Messung beendet. Speichere {frames_written} Zeilen in {filename}...")

    header = ["time"] + [f"CH{i}_hat1" for i in range(num_channels)] + [f"CH{i}_hat2" for i in range(num_channels)]
    # 2. Speichern mit Formatierung
    # %.3f für die Zeit (3 Nachkommastellen)
    # %d für die ADC-Werte (Integer)
    fmt = ['%.4f'] + ['%d'] * (2 * num_channels)
    
    np.savetxt(filename, all_data[:frames_written, :], delimiter=",", 
               header=",".join(header), comments='', fmt=fmt)

    print("Fertig!")



# --- HAUPTPROGRAMM ---
if __name__ == "__main__":
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
        
        # Jetzt kannst du hier einfach die Anzahl der Kanäle übergeben:
        pfad = "Messungen_2_Boards/messung_probe6.csv"
        measurement(hat1, hat2, duration_sec=2, filename=pfad, num_channels = 1, sampling_rate = 1000.0)

        