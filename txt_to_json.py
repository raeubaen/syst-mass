import pandas as pd
import numpy as np
import json

df = pd.read_csv("iJazZScalesSmearings_Zmmg_Run2_Stat_v5_scales.dat", sep="\t", header=None)
df.columns = ["f", "__", "eta_min", "eta_max", "r9_min", "r9_max", "pt_min", "pt_max", "gain", "correction", "syst"]
df = df[["f", "eta_min", "eta_max", "r9_min", "r9_max", "pt_min", "pt_max", "gain", "correction", "syst"]]
df = df[df.gain == 12]
df = df[df.f == 15]

df = df[["eta_min", "eta_max", "r9_min", "r9_max", "pt_min", "pt_max", "correction", "syst"]]

# Compute centers of fine bins
df["eta_center"] = 0.5 * (df["eta_min"] + df["eta_max"])
df["pt_center"]  = 0.5 * (df["pt_min"]  + df["pt_max"])
df["r9_center"]  = 0.5 * (df["r9_min"]  + df["r9_max"])

# Use the absolute value for coarse binning in eta
df["abs_eta"] = df["eta_center"].abs()

with open("bins.json") as f:
    bins = json.load(f)

# Assign coarse bins using abs(eta)
df["eta_bin"] = pd.cut(df["abs_eta"], bins=bins["eta_bins"], labels=False, right=False)
df["pt_bin"]  = pd.cut(df["pt_center"], bins=bins["pt_bins"], labels=False, right=False)
df["r9_bin"]  = pd.cut(df["r9_center"], bins=bins["r9_bins"], labels=False, right=False)

# Weighted average per coarse bin
grp = df.groupby(["pt_bin", "r9_bin", "eta_bin"], as_index=False).apply(
    lambda g: pd.Series({
      "correction": np.average(g["correction"]),
      "syst": np.average(g["syst"])
    })
)

# Build dicts
corrections = {}
systematics = {}

for _, row in grp.iterrows():
    key = f"({int(row.pt_bin)},{int(row.r9_bin)},{int(row.eta_bin)})"
    corrections[key] = float(row.correction)
    systematics[key] = float(row.syst)

ss_rebinned = {"corrections": corrections, "systematics": systematics}

with open("ss_rebinned.json", "w") as f:
    json.dump(ss_rebinned, f, indent=2)
