import matplotlib.pyplot as plt
import numpy as np

# =========================
# Dane
# =========================

engines = ["BQ", "MDB", "GP", "DDB", "PG"]

stages = [
    "Import danych",
    "Ustawienie SRID",
    "Walidacja geometrii",
    "Transformacja CRS",
    "Tworzenie indeksów (EPSG:2180)",
    "Tworzenie indeksów (EPSG:4326)",
    "Eksport danych",
]

data = np.array(
    [
        [87, 145, 0.0, 0.0, 0.0, 0.0, 26.10],
        [273, 493, 0.0, 0.0, 0.0, 571, 520],
        [86, 280, 68, 8.9, 190, 0.0, 262],
        [26.33, 0.0, 6.08, 13.74, 11.82, 0.0, 39.19],
        [220, 1065, 336, 1649, 84, 576, 61],
    ]
)

# =========================
# Wykres
# =========================

fig, ax = plt.subplots(figsize=(12, 6))

y_pos = np.arange(len(engines))
left = np.zeros(len(engines))

for i in range(len(stages)):
    ax.barh(y_pos, data[:, i], left=left, label=stages[i], edgecolor="white", linewidth=0.6)
    left += data[:, i]

# =========================
# Opisy i formatowanie
# =========================

ax.set_yticks(y_pos)
ax.set_yticklabels(engines, fontsize=16, fontweight="bold")

ax.set_xlabel("Czas preprocessingu [s]", fontsize=16, fontweight="bold")

# Ticki osi X
ax.tick_params(axis="x", labelsize=13)

# Margines po prawej
ax.set_xlim(0, data.sum(axis=1).max() * 1.05)

# Legenda
legend = ax.legend(
    title="Etap preprocessingu", loc="lower right", frameon=True, framealpha=0.95, fontsize=16
)

legend.get_title().set_fontsize(12)
legend.get_title().set_fontweight("bold")

for text in legend.get_texts():
    text.set_fontweight("bold")

# Siatka
ax.grid(axis="x", linestyle="--", alpha=0.4)

plt.tight_layout()
plt.show()
