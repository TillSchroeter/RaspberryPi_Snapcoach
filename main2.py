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
    

    frames_written = 0
    samples_per_block = 100  # Anzahl der Proben pro Block
    try:
        while frames_written < total_frames:
            # Wir fordern einen ganzen Block an
            result1 = hat1.a_in_scan_read(samples_per_channel=samples_per_block, timeout=0.1)
            result2 = hat2.a_in_scan_read(samples_per_channel=samples_per_block, timeout=0.1)
            
            # Berechne, wie viele vollständige Zeilen wir wirklich bekommen haben
            # (falls der Puffer am Ende der Messung weniger als 100 hergibt)
            num_received = len(result1.data) // num_channels
            
            if num_received > 0:
                # Berechne den Index-Bereich für diesen Block
                end_idx = min(frames_written + num_received, total_frames)
                count = end_idx - frames_written
                
                # Zeitstempel für diesen Block berechnen
                # Wir erzeugen eine Sequenz für die Zeitstempel dieses Blocks
                indices = np.arange(frames_written + 1, frames_written + count + 1)
                all_data[frames_written:end_idx, 0] = indices / sampling_rate
                
                # Daten in Array schreiben (Reshape der flachen Liste in 2D-Block)
                block1 = np.array(result1.data[:count * num_channels]).reshape(count, num_channels)
                block2 = np.array(result2.data[:count * num_channels]).reshape(count, num_channels)
                
                all_data[frames_written:end_idx, 1:1+num_channels] = block1
                all_data[frames_written:end_idx, 1+num_channels:] = block2
                
                frames_written += count
            
            # Ein kurzes Sleep ist weiterhin okay, aber bei Blöcken 
            # steuert die Hardware durch das Warten auf Daten den Takt.
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
    fmt = ['%.3f'] + ['%d'] * (2 * num_channels)
    
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
        pfad = "Messungen_2_Boards/messung_probe0.csv"
        measurement(hat1, hat2, duration_sec=1, filename=pfad, num_channels = 3, sampling_rate = 1000.0)