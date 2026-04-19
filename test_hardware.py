import time
from daqhats import OptionFlags, hat_list, HatIDs, mcc128, AnalogInputRange

# 1. Boards auflisten
board_list = hat_list(filter_by_id=HatIDs.MCC_128)

if not board_list:
    print("Keine MCC 128 Boards gefunden. Jumper checken!")
else:
    print(f"Gefundene Boards: {len(board_list)}")
    
    for entry in board_list:
        print(f"Board gefunden an Adresse: {entry.address}")
        
        # Board initialisieren
        hat = mcc128(entry.address)
        
        # 3. Spannung von Kanal 0 lesen (Test-Lesevorgang)
        # Wenn kein Signal anliegt, sollte hier etwas nahe 0V stehen
        value_cur = hat.a_in_read(0)
        print(f"Test-Messwert Kanal 0: {value_cur:.4f} V")

        # Bereich auf +/- 5V setzen
        hat.a_in_range_write(AnalogInputRange.BIP_5V)

        # Infos
        # print (f"Board-Info: {hat.info()}")

    
        print ("______________________________________________")
        # Wert lesen (mit NOSCALEDATA für den Rohwert)
        # Kanal 0, OptionFlags.NOSCALEDATA sorgt für den digitalen Wert
        raw_value = hat.a_in_read(0, options=OptionFlags.NOSCALEDATA)
        print(f"Digitaler Rohwert (0-65535): {raw_value}")

        # Zum Vergleich: Spannungswert (mit Default-Option)
        voltage = hat.a_in_read(0, options=OptionFlags.DEFAULT)
        print(f"Spannungswert (skaliert): {voltage:.4f} V")
