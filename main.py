import time
import csv
import numpy as np
from daqhats import hat_list, HatIDs, mcc128, AnalogInputRange, AnalogInputMode, OptionFlags
from PyQt6 import QtWidgets, uic

def measurement(hat1, hat2, duration_sec, filename, num_channels = 3, sampling_rate = 1000.0):
    # sampling_rate = 1000.0
    # num_channels = 3
    channel_mask = (0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F, 0x7F, 0xFF)  # Maske für alle acht Kanäle
    total_frames = int(round(duration_sec * sampling_rate)) # round um kleine latenzen aus der GUI auszugleichen
    frames_written = 0
    # Wir speichern die Zeit als float64 und die ADC-Werte als int32
    all_data = np.zeros((total_frames, 1 + 2 * num_channels), dtype=np.float64)


    print(f"Messung wird gestartet: {num_channels} Kanäle bei zwei Boards und {duration_sec}s...")


    hat1.a_in_scan_start(channel_mask = channel_mask[num_channels-1], samples_per_channel=0, 
                        sample_rate_per_channel=sampling_rate, 
                        options=OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA)

    hat2.a_in_scan_start(channel_mask = channel_mask[num_channels-1], samples_per_channel=0,
                        sample_rate_per_channel=sampling_rate, 
                        options=OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA | OptionFlags.EXTCLOCK)
    #samples_per_channel=0 bedeutet hier: Messe unendlich lange weiter, bis ich "Stopp" sage.


    samples_per_block = 100
    frames_written = 0
    try:
        while frames_written < total_frames:
            # 1. Daten abholen (wartet bis zu 0.1s auf die 100 Samples)
            result1 = hat1.a_in_scan_read(samples_per_channel=samples_per_block, timeout=0.1)
            result2 = hat2.a_in_scan_read(samples_per_channel=samples_per_block, timeout=0.1)
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

    return all_data


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
        pfad = "Messungen_2_Boards/messung_probe7.csv"
        all_data = measurement(hat1, hat2, duration_sec=1.00, filename=pfad, num_channels = 3, sampling_rate = 100.0)
        # print (all_data)
        # print (all_data.shape)

        