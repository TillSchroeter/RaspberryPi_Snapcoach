import time
import csv
import numpy as np
from daqhats import hat_list, HatIDs, mcc128, AnalogInputRange, AnalogInputMode, OptionFlags

# Automatische Masken-Berechnung:
    # Bei 3 Kanälen: (1 << 3) - 1 = 8 - 1 = 7 (binär 111)
    # Bei 6 Kanälen: (1 << 6) - 1 = 64 - 1 = 63 (binär 111111)
num_channels = 3
channel_mask = (1 << num_channels) - 1
print (f"Verwendete Kanalmaske: {channel_mask} (binär: {bin(channel_mask)})")