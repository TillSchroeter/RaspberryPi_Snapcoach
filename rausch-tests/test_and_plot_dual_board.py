import numpy as np
import time
import matplotlib.pyplot as plt
from daqhats import hat_list, HatIDs, mcc128, OptionFlags

def test_and_plot_dual_board(duration_sec=3.0, sampling_rate=1000.0):
    # 1. Boards initialisieren
    boards = hat_list(filter_by_id=HatIDs.MCC_128)
    if len(boards) < 2:
        print(f"Fehler: Es wurden nur {len(boards)} Boards gefunden. Es werden aber mindestens 2 benötigt!")
        return
    
    print(f"Gefundene Boards im Stack: {len(boards)}")
    
    # Annahme: Sortierung nach Hardware-Adresse (0 und 1)
    hat_links = mcc128(boards[0].address)
    hat_rechts = mcc128(boards[1].address)
    print(f"Board Links initialisiert auf Adresse: {boards[0].address}")
    print(f"Board Rechts initialisiert auf Adresse: {boards[1].address}")

    # Kanäle 0, 1, 2 und 4, 5, 6 aktiv via Maske 0x77 (6 Kanäle pro Board)
    channel_mask = 0x77
    num_channels = 6  
    
    total_frames = int(round(duration_sec * sampling_rate))
    
    # Haupt-Array: Spalte 0 = Zeit, Spalten 1-6 = Board Links, Spalten 7-12 = Board Rechts
    all_data = np.zeros((total_frames, 1 + 2 * num_channels), dtype=np.float64)
    
    print(f"\nStarte synchrone Testmessung für {duration_sec}s...")
    
    # Scan auf Board Links (Master - gibt die Clock vor)
    hat_links.a_in_scan_start(
        channel_mask=channel_mask,
        samples_per_channel=0,
        sample_rate_per_channel=sampling_rate,
        options=OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA
    )
    
    # Scan auf Board Rechts (Slave - lauscht auf externe Clock von Board 0)
    hat_rechts.a_in_scan_start(
        channel_mask=channel_mask,
        samples_per_channel=0,
        sample_rate_per_channel=sampling_rate,
        options=OptionFlags.CONTINUOUS | OptionFlags.NOSCALEDATA | OptionFlags.EXTCLOCK
    )
    
    samples_per_block = 100
    frames_written = 0
    
    try:
        while frames_written < total_frames:
            # Daten von beiden Boards abrufen
            result1 = hat_links.a_in_scan_read(samples_per_channel=samples_per_block, timeout=0.1)
            result2 = hat_rechts.a_in_scan_read(samples_per_channel=samples_per_block, timeout=0.1)
            
            # Anzahl gelesener Zeilen ermitteln
            actual_count1 = len(result1.data) // num_channels
            
            actual_count2 = len(result2.data) // num_channels
            
            # Minimum nehmen, um absolut synchron im Array zu bleiben
            actual_count = min(actual_count1, actual_count2)
            
            if actual_count > 0:
                if frames_written + actual_count > total_frames:
                    actual_count = total_frames - frames_written
                
                idx_end = frames_written + actual_count
                
                # Daten in 2D-Form bringen
                block1 = np.array(result1.data[:actual_count * num_channels], dtype=np.float64).reshape(actual_count, num_channels)
                block2 = np.array(result2.data[:actual_count * num_channels], dtype=np.float64).reshape(actual_count, num_channels)
                
                # Zeitstempel berechnen
                t_start = (frames_written + 1) / sampling_rate
                t_end = (frames_written + actual_count) / sampling_rate
                t_block = np.linspace(t_start, t_end, actual_count)
                
                # In das globale Speicher-Array einsortieren
                all_data[frames_written:idx_end, 0] = t_block                         # Zeit
                all_data[frames_written:idx_end, 1:1+num_channels] = block1           # Board Links
                all_data[frames_written:idx_end, 1+num_channels:] = block2            # Board Rechts
                
                frames_written += actual_count
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nMessung durch Benutzer abgebrochen!")
    finally:
        # Hardware sauber stoppen
        hat_links.a_in_scan_stop()
        hat_rechts.a_in_scan_stop()
        hat_links.a_in_scan_cleanup()
        hat_rechts.a_in_scan_cleanup()
        print("Beide Scans gestoppt und Ressourcen freigegeben.")

    if frames_written == 0:
        print("Keine Daten erfasst.")
        return

    # Daten-Vektoren separieren
    time_vec = all_data[:frames_written, 0]
    
    # Board Links (Spalten 1 bis 6)
    b1_fx, b1_fy, b1_fz = all_data[:frames_written, 1], all_data[:frames_written, 2], all_data[:frames_written, 3]
    b1_mx, b1_my, b1_mz = all_data[:frames_written, 4], all_data[:frames_written, 5], all_data[:frames_written, 6]
    
    # Board Rechts (Spalten 7 bis 12)
    b2_fx, b2_fy, b2_fz = all_data[:frames_written, 7], all_data[:frames_written, 8], all_data[:frames_written, 9]
    b2_mx, b2_my, b2_mz = all_data[:frames_written, 10], all_data[:frames_written, 11], all_data[:frames_written, 12]

    # 2. Text-Analyse im Terminal ausgeben
    print("\n=== STATISTISCHE RAUSCHANALYSE (Standardabweichung) ===")
    print("[BOARD LINKS]")
    print(f"  CH0 (Fx1) -> Rauschen (StdDev): {np.std(b1_fx):8.4f} | CH4 (Mx1) -> Rauschen (StdDev): {np.std(b1_mx):8.4f}")
    print(f"  CH1 (Fy1) -> Rauschen (StdDev): {np.std(b1_fy):8.4f} | CH5 (My1) -> Rauschen (StdDev): {np.std(b1_my):8.4f}")
    print(f"  CH2 (Fz1) -> Rauschen (StdDev): {np.std(b1_fz):8.4f} | CH6 (Mz1) -> Rauschen (StdDev): {np.std(b1_mz):8.4f}")
    print("\n[BOARD RECHTS]")
    print(f"  CH0 (Fx2) -> Rauschen (StdDev): {np.std(b2_fx):8.4f} | CH4 (Mx2) -> Rauschen (StdDev): {np.std(b2_mx):8.4f}")
    print(f"  CH1 (Fy2) -> Rauschen (StdDev): {np.std(b2_fy):8.4f} | CH5 (My2) -> Rauschen (StdDev): {np.std(b2_my):8.4f}")
    print(f"  CH2 (Fz2) -> Rauschen (StdDev): {np.std(b2_fz):8.4f} | CH6 (Mz2) -> Rauschen (StdDev): {np.std(b2_mz):8.4f}")

    # 3. Grafische Darstellung mit 4 Subplots
    print("\nErstelle Graphen... Bitte warten.")
    fig, axs = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    
    # Subplot 1: Board Links - Kräfte
    axs[0].plot(time_vec, b1_fx, label="Fx1 (CH0)", alpha=0.7)
    axs[0].plot(time_vec, b1_fy, label="Fy1 (CH1)", alpha=0.7)
    axs[0].plot(time_vec, b1_fz, label="Fz1 (CH2)", alpha=0.7)
    axs[0].set_title("BOARD LINKS: Analogsignale der Kräfte", fontsize=11, fontweight='bold')
    axs[0].set_ylabel("Digit-Wert")
    axs[0].grid(True, linestyle="--", alpha=0.5)
    axs[0].legend(loc="upper right")
    
    # Subplot 2: Board Links - Momente
    axs[1].plot(time_vec, b1_mx, label="Mx1 (CH4)", color='purple', alpha=0.7)
    axs[1].plot(time_vec, b1_my, label="My1 (CH5)", color='orange', alpha=0.7)
    axs[1].plot(time_vec, b1_mz, label="Mz1 (CH6)", color='brown', alpha=0.7)
    axs[1].set_title("BOARD LINKS: Analogsignale der Momente", fontsize=11, fontweight='bold')
    axs[1].set_ylabel("Digit-Wert")
    axs[1].grid(True, linestyle="--", alpha=0.5)
    axs[1].legend(loc="upper right")
    
    # Subplot 3: Board Rechts - Kräfte
    axs[2].plot(time_vec, b2_fx, label="Fx2 (CH0)", linestyle="--", alpha=0.7)
    axs[2].plot(time_vec, b2_fy, label="Fy2 (CH1)", linestyle="--", alpha=0.7)
    axs[2].plot(time_vec, b2_fz, label="Fz2 (CH2)", linestyle="--", alpha=0.7)
    axs[2].set_title("BOARD RECHTS: Analogsignale der Kräfte", fontsize=11, fontweight='bold')
    axs[2].set_ylabel("Digit-Wert")
    axs[2].grid(True, linestyle="--", alpha=0.5)
    axs[2].legend(loc="upper right")
    
    # Subplot 4: Board Rechts - Momente
    axs[3].plot(time_vec, b2_mx, label="Mx2 (CH4)", color='purple', linestyle="--", alpha=0.7)
    axs[3].plot(time_vec, b2_my, label="My2 (CH5)", color='orange', linestyle="--", alpha=0.7)
    axs[3].plot(time_vec, b2_mz, label="Mz2 (CH6)", color='brown', linestyle="--", alpha=0.7)
    axs[3].set_title("BOARD RECHTS: Analogsignale der Momente", fontsize=11, fontweight='bold')
    axs[3].set_xlabel("Zeit (Sekunden)")
    axs[3].set_ylabel("Digit-Wert")
    axs[3].grid(True, linestyle="--", alpha=0.5)
    axs[3].legend(loc="upper right")
    
    plt.tight_layout()
    plt.savefig("dual_board_signals4.png", dpi=300)  # Optional: Speichern der Grafik
    # plt.show()

if __name__ == "__main__":
    print("starte in 2 Sekunden...")
    time.sleep(2)  # Kurze Pause vor Start
    print ("Starte Test und Plot für ein einzelnes Board...")
    test_and_plot_dual_board(duration_sec=5.0, sampling_rate=1000.0)