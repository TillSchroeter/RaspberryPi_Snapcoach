import time
import csv
import numpy as np
from daqhats import hat_list, HatIDs, mcc128, AnalogInputRange, AnalogInputMode, OptionFlags
import os

# kern 1 reservieren, damit die Messung nicht durch andere Prozesse gestört wird
# os.sched_setaffinity(0, {1})

# Hilfsfunktion zur Paket-Bereinigung
def clean_data(result, channels):
    data = np.array(result.data)
    num_full_samples = len(data) // channels
    return data[:num_full_samples * channels].reshape(-1, channels)

def measurement(hat1, hat2, duration_sec, filename, num_channels = 3, sampling_rate = 1000.0):
    # sampling_rate = 1000.0
    # num_channels = 3
    channel_mask = (0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F, 0x7F, 0xFF)  # Maske für alle sechs gebrauchte Kanäle
    csv_columns_hat1 = [f"CH{i}_hat1" for i in range(num_channels)]
    csv_columns_hat2 = [f"CH{i}_hat2" for i in range(num_channels)]
    total_frames = int(duration_sec * sampling_rate)
    frames_written = 0

    # Zwischenspeicher initialisieren für den Fall, dass ein Board schneller liefert
    buffer1 = np.array([]).reshape(0, num_channels)
    buffer2 = np.array([]).reshape(0, num_channels)

    print(f"Messung wird gestartet: {num_channels} Kanäle bei zwei Boards und {duration_sec}s...")

    hat1.a_in_scan_start(channel_mask = channel_mask[num_channels-1], samples_per_channel=0, 
                        sample_rate_per_channel=sampling_rate, 
                        options=OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA)

    hat2.a_in_scan_start(channel_mask = channel_mask[num_channels-1], samples_per_channel=0, 
                        sample_rate_per_channel=sampling_rate, 
                        options=OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA)
    

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["time"] + csv_columns_hat1 + csv_columns_hat2)
        
        try:
            while frames_written < total_frames:
                # Daten lesen
                result1 = hat1.a_in_scan_read(samples_per_channel=-1, timeout=0.1)
                result2 = hat2.a_in_scan_read(samples_per_channel=-1, timeout=0.1)
                
                # An Puffer anhängen
                if len(result1.data) > 0:
                    buffer1 = np.vstack((buffer1, np.array(result1.data).reshape(-1, num_channels)))
                if len(result2.data) > 0:
                    buffer2 = np.vstack((buffer2, np.array(result2.data).reshape(-1, num_channels)))
                
                # Schreiben, wenn beide Boards Daten geliefert haben
                if buffer1.shape[0] > 0 and buffer2.shape[0] > 0:
                    process_rows = min(buffer1.shape[0], buffer2.shape[0])
                    
                    # Begrenzung auf das Ziel
                    remaining = total_frames - frames_written
                    process_rows = min(process_rows, remaining)
                    
                    # Daten für den Schreibblock extrahieren
                    data_to_write1 = buffer1[:process_rows, :]
                    data_to_write2 = buffer2[:process_rows, :]
                    
                    # Zeitstempel
                    current_times = (np.arange(process_rows) + 1 + frames_written) / sampling_rate
                    
                    # Zusammenfügen und schreiben
                    output_block = np.column_stack((current_times, data_to_write1, data_to_write2))
                    writer.writerows(output_block)
                    
                    # Puffer bereinigen (Rest behalten)
                    buffer1 = buffer1[process_rows:, :]
                    buffer2 = buffer2[process_rows:, :]
                    
                    frames_written += process_rows
                
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("Abbruch!")
            
    hat1.a_in_scan_stop()
    hat2.a_in_scan_stop()
    hat1.a_in_scan_cleanup()
    hat2.a_in_scan_cleanup()
    print(f"Messung beendet. Exakt {frames_written} Zeilen geschrieben.")


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
        pfad = "Messungen_2_Boards/messung_probe1.csv"
        measurement(hat1, hat2, duration_sec=2, filename=pfad, num_channels = 3, sampling_rate = 1000.0)
