import time
import csv
import numpy as np
from daqhats import hat_list, HatIDs, mcc128, AnalogInputRange, AnalogInputMode, OptionFlags
import os

# kern 1 reservieren, damit die Messung nicht durch andere Prozesse gestört wird
# os.sched_setaffinity(0, {1})


def measurement(hat, duration_sec, filename, num_channels, sampling_rate = 1000.0):
    sampling_rate = 1000.0
    # num_channels = 3
    channel_mask = sum([1 << i for i in range(num_channels)])  # Dynamische Berechnung der Kanalmaske
    total_frames = int(duration_sec * sampling_rate)
    
    hat.a_in_scan_start(channel_mask=channel_mask, samples_per_channel=0, 
                        sample_rate_per_channel=sampling_rate, 
                        options=OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA)
    
    frames_written = 0
    print(f"Messung läuft: {num_channels} Kanäle, {duration_sec}s...")
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["time", "CH0_raw", "CH1_raw", "CH2_raw"])
        
        try:
            while frames_written < total_frames:
                result = hat.a_in_scan_read(samples_per_channel=-1, timeout=0.1)
                
                if len(result.data) > 0:
                    # 1. Datenmatrix formen (n x 3)
                    data_matrix = np.array(result.data).reshape(-1, num_channels)
                    print (len(result.data), " Datenpunkte gelesen")
                    print (result.data[:9], " Erste 10 Datenpunkte")

                    # 2. Überhang abschneiden, falls wir über total_frames kommen
                    remaining = total_frames - frames_written
                    if data_matrix.shape[0] > remaining:
                        data_matrix = data_matrix[:remaining, :]
                    
                    # 3. Zeitstempel für diesen Block berechnen
                    current_times = (np.arange(data_matrix.shape[0]) + 1 + frames_written) / sampling_rate
                    
                    # 4. Zusammenfügen und als Block schreiben
                    output_block = np.column_stack((current_times, data_matrix))
                    writer.writerows(output_block)
                    
                    # 5. Counter erhöhen
                    frames_written += data_matrix.shape[0]
                    print (f"{data_matrix.shape[0]} Frames")    


                # time.sleep(0.01)
        except KeyboardInterrupt:
            print("Abbruch!")
            
    hat.a_in_scan_stop()
    hat.a_in_scan_cleanup()
    print(f"Messung beendet. Exakt {frames_written} Zeilen geschrieben.")


# --- HAUPTPROGRAMM ---
if __name__ == "__main__":
    board_list = hat_list(filter_by_id=HatIDs.MCC_128)
    if not board_list:
        print("Kein Board gefunden!")
    else:
        hat1 = mcc128(board_list[1].address)
        hat1.a_in_mode_write(AnalogInputMode.SE)
        hat1.a_in_range_write(AnalogInputRange.BIP_5V)
        
        # Jetzt kannst du hier einfach die Anzahl der Kanäle übergeben:
        pfad = "Messungen_multiKanal/egal.csv"
        measurement(hat1, duration_sec=0.5, filename=pfad, num_channels=3)
