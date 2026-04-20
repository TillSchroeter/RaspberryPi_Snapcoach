from daqhats import OptionFlags, hat_list, HatIDs, mcc128, AnalogInputRange, AnalogInputMode
import time
import numpy as np
import csv

import time
import csv
from daqhats import hat_list, HatIDs, mcc128, AnalogInputRange, OptionFlags

def measurement(hat, duration_sec, filename):
    sampling_rate = 1000.0
    total_samples = int(duration_sec * sampling_rate)
    
    # Vorberechnung der Kalibrierung (einmalig vor dem Scan)
    info = hat.info()
    range_index = 1 # BIP_5V
    min_v = info.AI_MIN_VOLTAGE[range_index]
    max_v = info.AI_MAX_VOLTAGE[range_index]
    min_code = info.AI_MIN_CODE
    max_code = info.AI_MAX_CODE
    cal = hat.calibration_coefficient_read(AnalogInputRange.BIP_5V)

    # Scan starten
    hat.a_in_scan_start(channel_mask=0x01, samples_per_channel=0, 
                        sample_rate_per_channel=sampling_rate, 
                        options=OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA)
    
    samples_read = 0
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["time", "raw_value", "voltage_calc", "voltage_default"])
        
        try:
            while samples_read < total_samples:
                result = hat.a_in_scan_read(samples_per_channel=-1, timeout=0.1)
                if len(result.data) > 0:
                    for raw in result.data:
                        time_val = samples_read / sampling_rate
                        # Umrechnungen
                        voltage_calc = min_v + (raw - min_code) * (max_v - min_v) / (max_code - min_code)
                        voltage_default = (raw * cal.slope + cal.offset)
                        
                        writer.writerow([f"{time_val:.3f}", raw, f"{voltage_calc:.4f}", f"{voltage_default:.4f}"])
                        samples_read += 1
                        if samples_read >= total_samples: break
                time.sleep(0.01)
        except KeyboardInterrupt: pass
            
    hat.a_in_scan_stop()
    hat.a_in_scan_cleanup()
    print(f"Messung beendet: {samples_read} Samples.")

# --- HAUPTPROGRAMM (Hier startet dein Script) ---
if __name__ == "__main__":
    board_list = hat_list(filter_by_id=HatIDs.MCC_128)
    if not board_list:
        print("Kein Board gefunden!")
    else:
        hat1 = mcc128(board_list[0].address)
        hat1.a_in_mode_write(AnalogInputMode.SE) # WICHTIG: Single-Ended Modus setzen
        hat1.a_in_range_write(AnalogInputRange.BIP_5V)
        
        # Aufruf der Funktion
        pfad = "Messungen/messung_probe5.csv"
        measurement(hat1, duration_sec=10, filename=pfad)