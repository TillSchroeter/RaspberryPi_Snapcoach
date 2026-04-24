import pandas as pd
import matplotlib.pyplot as plt

def plot_messung(filename):
    # CSV einlesen
    df = pd.read_csv(filename + ".csv")
    
    # Plot erstellen (2 Zeilen, 1 Spalte)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # HAT 1 plotten
    ax1.plot(df['time'], df['CH0_hat1'], label='CH0_hat1')
    ax1.plot(df['time'], df['CH1_hat1'], label='CH1_hat1')
    ax1.plot(df['time'], df['CH2_hat1'], label='CH2_hat1')
    ax1.set_xlim(0, 0.1)
    ax1.set_title('MCC 128 - Board 1')
    ax1.set_ylabel('ADC Rohwert')
    ax1.legend()
    ax1.grid(True)
    
    # HAT 2 plotten
    ax2.plot(df['time'], df['CH0_hat2'], label='CH0_hat2')
    ax2.plot(df['time'], df['CH1_hat2'], label='CH1_hat2')
    ax2.plot(df['time'], df['CH2_hat2'], label='CH2_hat2')
    ax2.set_xlim(0, 0.1)
    ax2.set_title('MCC 128 - Board 2')
    ax2.set_xlabel('Zeit [s]')
    ax2.set_ylabel('ADC Rohwert')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    # Plot speichern
    plt.savefig(filename + '.png')
    print("Plot wurde als 'messung_plot.png' gespeichert.")

def plot_messung_6_channels(filename):
    # CSV einlesen
    df = pd.read_csv(filename + ".csv")
    
    # Plot erstellen (2 Zeilen, 1 Spalte)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # HAT 1 plotten
    ax1.plot(df['time'], df['CH0_hat1'], label='CH0_hat1')
    # ax1.plot(df['time'], df['CH1_hat1'], label='CH1_hat1')
    # ax1.plot(df['time'], df['CH2_hat1'], label='CH2_hat1')
    # ax1.plot(df['time'], df['CH3_hat1'], label='CH3_hat1')
    # ax1.plot(df['time'], df['CH4_hat1'], label='CH4_hat1')
    # ax1.plot(df['time'], df['CH5_hat1'], label='CH5_hat1')

    # ax1.set_xlim(0, 0.1)
    ax1.set_title('MCC 128 - Board 1')
    ax1.set_ylabel('ADC Rohwert')
    ax1.legend()
    ax1.grid(True)
    
    # HAT 2 plotten
    ax2.plot(df['time'], df['CH0_hat2'], label='CH0_hat2')
    # ax2.plot(df['time'], df['CH1_hat2'], label='CH1_hat2')
    # ax2.plot(df['time'], df['CH2_hat2'], label='CH2_hat2')
    # ax2.plot(df['time'], df['CH3_hat2'], label='CH3_hat2')
    # ax2.plot(df['time'], df['CH4_hat2'], label='CH4_hat2')
    # ax2.plot(df['time'], df['CH5_hat2'], label='CH5_hat2')

    # ax2.set_xlim(0, 0.1)
    ax2.set_title('MCC 128 - Board 2')
    ax2.set_xlabel('Zeit [s]')
    ax2.set_ylabel('ADC Rohwert')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    # Plot speichern
    plt.savefig(filename + '.png')
    print("Plot wurde als 'messung_plot.png' gespeichert.")


# Dateipfad hier anpassen
plot_messung_6_channels('Messungen_2_Boards/messung_probe4')