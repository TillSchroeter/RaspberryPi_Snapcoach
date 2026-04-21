import matplotlib.pyplot as plt
import pandas as pd

#Csv importieren
speicherpfad = "Messungen_multiKanal/messung_probe8"
df = pd.read_csv(speicherpfad + ".csv")
# print (df.head())

# digitalen ADC Wert in Newton umrechnen
# Definitionen der Kapazitäten (bitte an Ihr Kalibrierungsblatt anpassen!)
# Hier beispielhaft für Ihre Annahmen
capacity = 10000    # Für Fz
gain = 1        # Verstärkung (bitte anpassen, falls verwendet)

# Alle Spalten filtern, die mit "CH" anfangen (deine Raw-Daten)
# channel_cols = [col for col in df.columns if col.startswith("CH")]

# # Vektorisierte Umrechnung auf alle Kanäle gleichzeitig
# # Formel: ((raw - 32768) / 32768) * (Capacity / Gain)
# # Wir erstellen neue Spalten, z.B. mit dem Suffix "_N"
# for col in channel_cols:
#     new_col_name = col.replace("_raw", "_N")
#     df[new_col_name] = ((df[col] - 32768) / 32768) * (capacity / gain)

df["CH0_N"] = ((df["CH0_raw"] - 32768) / 32768) * (capacity / gain)
df["CH1_N"] = ((df["CH1_raw"] - 32768) / 32768) * (capacity / gain)
df["CH2_N"] = ((df["CH2_raw"] - 32768) / 32768) * (capacity / gain)
# df["CH3_N"] = ((df["CH3_raw"] - 32768) / 32768) * (capacity / gain)
# df["CH4_N"] = ((df["CH4_raw"] - 32768) / 32768) * (capacity / gain)
# df["CH5_N"] = ((df["CH5_raw"] - 32768) / 32768) * (capacity / gain)


# Plot erstellen
plt.figure(figsize=(10, 5))
plt.plot(df["time"], df["CH0_N"], label="CH0_z")
plt.plot(df["time"], df["CH1_N"], label="CH1_y")
plt.plot(df["time"], df["CH2_N"], label="CH2_x")
# plt.plot(df["time"], df["CH3_N"], label="CH3")
# plt.plot(df["time"], df["CH4_N"], label="CH4")
# plt.plot(df["time"], df["CH5_N"], label="CH5")
plt.title('Kraftmessung über Zeit')
plt.xlabel('Zeit (s)')
plt.ylabel('Kraft (N)')
# plt.xlim(0, 0.25)
# plt.ylim(0, 500)
plt.grid()
plt.legend()
plt.tight_layout()
plt.savefig(speicherpfad)  # Plot als PNG speichern
print(f"Plot gespeichert als '{speicherpfad}'")
# # plt.show()