import matplotlib.pyplot as plt
import pandas as pd

#Csv importieren
speicherpfad = "Messungen/messung_probe6"
df = pd.read_csv(speicherpfad + ".csv")
print (df.head())

# digitalen ADC Wert in Newton umrechnen
# Definitionen der Kapazitäten (bitte an Ihr Kalibrierungsblatt anpassen!)
# Hier beispielhaft für Ihre Annahmen
capacity = 10000    # Für Fz
gain = 1        # Verstärkung (bitte anpassen, falls verwendet)

# 3. Vektorisierte Umrechnung
# Formel: ((raw - 32768) / 32768) * (Capacity / Gain)
df_newton = df.copy()
df["channel_0_Newton"] = ((df["raw_value"].values - 32768) / 32768) * (capacity / gain)

# print (df["channel_0_Newton"])
# print(df)

# Plot erstellen
plt.figure(figsize=(10, 5))
plt.plot(df['time'], df['channel_0_Newton'], label='Kanal 0')
plt.title('Kraftmessung über Zeit')
plt.xlabel('Zeit (s)')
plt.ylabel('Kraft (N)')
plt.ylim(-100, 1000)
plt.grid()
plt.legend()
plt.tight_layout()


plt.savefig(speicherpfad)  # Plot als PNG speichern
print(f"Plot gespeichert als '{speicherpfad}'")
# plt.show()