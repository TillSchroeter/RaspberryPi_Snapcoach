import numpy as np
import time
import matplotlib.pyplot as plt
from daqhats import hat_list, HatIDs, mcc128, OptionFlags

def test_and_plot_single_board(duration_sec=3.0, sampling_rate=1000.0):
    # 1. Boards suchen
    boards = hat_list(filter_by_id=HatIDs.MCC_128)
    if not boards:
        print("Fehler: Kein MCC 128 Board gefunden!")
        return
    
    print(f"Gefundene Boards: {len(boards)}")
    address = boards[0].address
    board = mcc128(address)
    print(f"Nutze Board auf Adresse: {address}")

    # Kanäle 0, 1, 2 und 4, 5, 6 aktiv via Maske 0x77 (insgesamt 6 Kanäle)
    channel_mask = 0x77
    num_channels = 6  
    
    total_frames = int(round(duration_sec * sampling_rate))
    
    # Haupt-Array vorbereiten: Spalte 0 für Zeit, Spalten 1-6 für die Kanäle
    all_data = np.zeros((total_frames, 1 + num_channels), dtype=np.float64)
    
    print(f"Starte Testmessung für {duration_sec}s ({total_frames} Frames)...")
    
    # Scan starten
    board.a_in_scan_start(
        channel_mask=channel_mask,
        samples_per_channel=0,
        sample_rate_per_channel=sampling_rate,
        options=OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA
    )
    
    samples_per_block = 100
    frames_written = 0
    
    try:
        while frames_written < total_frames:
            result = board.a_in_scan_read(samples_per_channel=samples_per_block, timeout=0.1)
            actual_count = len(result.data) // num_channels
            
            if actual_count > 0:
                if frames_written + actual_count > total_frames:
                    actual_count = total_frames - frames_written
                
                idx_end = frames_written + actual_count
                
                # Daten in 2D-Form bringen
                block = np.array(result.data[:actual_count * num_channels], dtype=np.float64).reshape(actual_count, num_channels)
                
                # Zeitstempel berechnen
                t_start = (frames_written + 1) / sampling_rate
                t_end = (frames_written + actual_count) / sampling_rate
                t_block = np.linspace(t_start, t_end, actual_count)
                
                # In das Haupt-Array einfügen
                all_data[frames_written:idx_end, 0] = t_block       # Spalte 0: Zeit
                all_data[frames_written:idx_end, 1:] = block        # Spalten 1-6: Kanäle
                
                frames_written += actual_count
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nMessung durch Benutzer abgebrochen!")
    finally:
        board.a_in_scan_stop()
        board.a_in_scan_cleanup()
        print("Scan gestoppt.")

    if frames_written == 0:
        print("Keine Daten erfasst.")
        return

    # Zeitvektor und Kanäle extrahieren
    time_vec = all_data[:frames_written, 0]
    # Indizes im all_data-Array (Spalte 0 ist Zeit, daher +1)
    ch0 = all_data[:frames_written, 1]  # Fx
    ch1 = all_data[:frames_written, 2]  # Fy
    ch2 = all_data[:frames_written, 3]  # Fz
    ch4 = all_data[:frames_written, 4]  # Mx
    ch5 = all_data[:frames_written, 5]  # My
    ch6 = all_data[:frames_written, 6]  # Mz

    # 2. Text-Analyse im Terminal ausgeben
    print("\n=== STATISTISCHE RAUSCHANALYSE (Standardabweichung) ===")
    channels_dict = {"CH0 (Fx)": ch0, "CH1 (Fy)": ch1, "CH2 (Fz)": ch2, 
                     "CH4 (Mx)": ch4, "CH5 (My)": ch5, "CH6 (Mz)": ch6}
    
    for name, data in channels_dict.items():
        std_dev = np.std(data)
        print(f"{name} -> Rauschen (StdDev): {std_dev:8.4f} LSB/Volt")

    # 3. Grafische Darstellung mit Matplotlib
    print("\nErstelle Graphen... Bitte warte, bis sich das Fenster öffnet.")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # Graph 1: Kräfte (CH0, CH1, CH2)
    ax1.plot(time_vec, ch0, label="CH0 (Fx)", alpha=0.7)
    ax1.plot(time_vec, ch1, label="CH1 (Fy)", alpha=0.7)
    ax1.plot(time_vec, ch2, label="CH2 (Fz)", alpha=0.7)
    ax1.set_title("Analogsignale der Kräfte (Kanal 0, 1, 2)", fontsize=12, fontweight='bold')
    ax1.set_ylabel("Spannung / Digit-Wert")
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="upper right")
    
    # Graph 2: Momente (CH4, CH5, CH6)
    ax2.plot(time_vec, ch4, label="CH4 (Mx)", color='purple', alpha=0.7)
    ax2.plot(time_vec, ch5, label="CH5 (My)", color='orange', alpha=0.7)
    ax2.plot(time_vec, ch6, label="CH6 (Mz)", color='brown', alpha=0.7)
    ax2.set_title("Analogsignale der Momente (Kanal 4, 5, 6)", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Zeit (Sekunden)")
    ax2.set_ylabel("Spannung / Digit-Wert")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="upper right")
    
    plt.tight_layout()
    plt.savefig("single_board_measurement2.png", dpi=300)
    plt.show()

if __name__ == "__main__":
    # Misst für 5 Sekunden bei 1000 Hz und plottet danach
    print("starte in 2 Sekunden...")
    time.sleep(2)  # Kurze Pause vor Start
    print ("Starte Test und Plot für ein einzelnes Board...")
    test_and_plot_single_board(duration_sec=5.0, sampling_rate=1000.0)