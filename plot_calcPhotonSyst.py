import matplotlib.pyplot as plt
import json

dct = json.load(open("output.json", "r"))

# -------------------------
# Explicit bin label mappings
# -------------------------
R9_MAP = {
    "R9_bin_0": "LowR9",
    "R9_bin_1": "HighR9",
}

PT_MAP = {
    "pT_bin_0": "LowPt",
    "pT_bin_1": "HighPt",
}

ETA_MAP = {
    "eta_bin0": "CentralEB",
    "eta_bin1": "OuterEB",
    "eta_bin2": "EE",
}


for cat in dct:
  # -------------------------
  # Your JSON dictionary
  # -------------------------
  data = dct[cat]["syst_per_cat_and_bin"]

  # -------------------------
  # Plot
  # -------------------------
  fig, ax = plt.subplots(figsize=(9, 7))

  for r9_bin, r9_dict in data.items():
      for pt_bin, pt_dict in r9_dict.items():
          for eta_key, nominal in pt_dict.items():

              # skip calcPhotonSyst entries
              if eta_key.endswith("_calcPhotonSyst"):
                  continue

              calc_key = eta_key + "_calcPhotonSyst"
              calc_val = pt_dict.get(calc_key)

              # safety
              if calc_val is None or nominal == 0:
                  continue

              ratio = nominal / calc_val
              nominal *= 125e3

              label = (
                  f"{R9_MAP[r9_bin]}, "
                  f"{PT_MAP[pt_bin]}, "
                  f"{ETA_MAP[eta_key]}"
              )

              ax.scatter(nominal, ratio, s=60)
              ax.annotate(
                  label,
                  (nominal, ratio),
                  xytext=(5, 5),
                  textcoords="offset points",
                  fontsize=9
              )

  # -------------------------
  # Styling
  # -------------------------
  ax.set_title(cat)
  ax.set_xlabel("Semi-analytical value [MeV]", fontsize=20, labelpad=20)
  ax.set_ylabel("Semi-analytical / calcPhotonSyst", fontsize=20, labelpad=20)

  ax.grid(True, which="both", linestyle="--", alpha=0.4)

  plt.tight_layout()
  plt.savefig(f"{cat}_syst_ratio_vs_nominal.png", dpi=300)
  plt.close()

