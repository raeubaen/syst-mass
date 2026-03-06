import pickle
import ROOT
import json
import argparse
from array import array
import math

ROOT.gROOT.SetBatch(True)

# ------------------------------
# Argument parser
# ------------------------------
parser = argparse.ArgumentParser(description="Produce 2D histograms for categories.")

parser.add_argument("--bins", required=True, help="Input bins JSON file")
parser.add_argument("--scale", required=True, help="Input scale JSON file")
parser.add_argument("--categories", required=True, help="JSON file listing category TTrees")
parser.add_argument("--processes", required=True, help="ROOT file containing all categories")
parser.add_argument("--make-comparisons", action="store_true")

args = parser.parse_args()

# ------------------------------
# Load JSONs
# ------------------------------
with open(args.bins) as f:
    bins = json.load(f)

with open(args.categories) as f:
    categories = json.load(f)

eta_bins = bins["eta_bins"]
pt_bins  = bins["pt_bins"]
r9_bins  = bins["r9_bins"]
mass_bins = bins["mass_bins"]

with open(args.scale) as f:
    scale = json.load(f)

corr_map = scale["corrections"]   # keys: i_ptL_i_r9L_i_ptS_i_r9S

## THIS SWITCHES THE CODE FROM SYST. TO CORRECTIONS -> Contributions HAVE TO BE ADDED LINEARLY AFTERWARDS!!
syst_map = scale["corrections"]

syst_per_bin_cat = {}
for cat in categories:
  syst_per_bin_cat[cat] = {}
  for r9_bin in range(len(r9_bins)-1):
    syst_per_bin_cat[cat][f"R9_bin_{r9_bin}"] = {}
    for pt_bin in range(len(pt_bins)-1):
      syst_per_bin_cat[cat][f"R9_bin_{r9_bin}"][f"pT_bin_{pt_bin}"] = {}
      for eta_bin in range(len(eta_bins)-1):
        syst_per_bin_cat[cat][f"R9_bin_{r9_bin}"][f"pT_bin_{pt_bin}"][f"eta_bin{eta_bin}"] = 0


with open(args.processes) as f:
    processes = json.load(f)


root_infiles = {}
for proc in processes:
  root_infiles[proc] = ROOT.TFile.Open(processes[proc])


# Output JSON
output = {}

f = ROOT.TFile("out.root", "recreate")

syst_per_cat_dict = {}

yields_per_process_cat = {}

# -------------------------------------------------------------------------
# Loop on categories (trees)
# -------------------------------------------------------------------------
for i_cat, cat in enumerate(categories):

    print(f"processing: {cat}")
    yields_per_process_cat[cat] = {}

    #this part is hardcoded for now
    with open(f"calcPhotonSyst_pickles/{cat}.pkl", "rb") as f_pkl:
      pkl = pickle.load(f_pkl)


    hist_1d = ROOT.TH1F(
        f"histo_{cat}_1d", f"histo_{cat}",
        len(mass_bins) - 1 , array('f', mass_bins)            # you choose these bins
    )

    for proc in processes:
    # Create TH3F: mass : eta1 : eta2

      hist_1d_proc = ROOT.TH1F(
        f"histo_{cat}_1d_{proc}", f"histo_{cat}_{proc}",
        len(mass_bins) - 1 , array('f', mass_bins)            # you choose these bins
      )

      tree = root_infiles[proc].Get(f"tagsDumper/trees/{proc}_125_13TeV_{cat}")
      if not tree:
        print(f"WARNING: TTree '{cat}' not found.")
        print(processes[proc], f"tagsDumper/trees/{proc}_125_13TeV_{cat}")
        continue

     # Fill histogram
      tree.Draw(f"CMS_hgg_mass>>histo_{cat}_1d_{proc}", "", "goff")
      yields_per_process_cat[cat][proc] = hist_1d_proc.Integral()
      hist_1d.Add(hist_1d_proc)


    syst_per_cat_sum = 0
    weight_per_cat_sum = 0

    output[cat] = {}

    output[cat]["mass_res"] = 0
    output[cat]["n_ev"] = 0

    for i_ptL in range(len(pt_bins)-1):
        for i_r9L in range(len(r9_bins)-1):
            for i_ptS in range(len(pt_bins)-1):
                for i_r9S in range(len(r9_bins)-1):

                    tag = f"ptL{i_ptL}_r9L{i_r9L}_ptS{i_ptS}_r9S{i_r9S}"
                    hname = f"h_{cat}_{tag}"

                    # Selection using the SAME bins for leading and subleading
                    sel = (
                        f"leadPt>{pt_bins[i_ptL]} && leadPt<{pt_bins[i_ptL+1]} && "
                        f"leadR9>{r9_bins[i_r9L]} && leadR9<{r9_bins[i_r9L+1]} && "
                        f"subleadPt>{pt_bins[i_ptS]} && subleadPt<{pt_bins[i_ptS+1]} && "
                        f"subleadR9>{r9_bins[i_r9S]} && subleadR9<{r9_bins[i_r9S+1]}"
                    )

                    # Create TH3F: mass : eta1 : eta2
                    hist = ROOT.TH3F(
                        hname, hname,
                        len(eta_bins) - 1, array('f', eta_bins),     # pho1_eta axis
                        len(eta_bins) - 1, array('f', eta_bins),     # pho2_eta axis
                        len(mass_bins) - 1 , array('f', mass_bins)            # you choose these bins
                    )

                    for proc in processes:
                      # Create TH3F: mass : eta1 : eta2
                      hist_proc = ROOT.TH3F(
                          f"{hname}_{proc}", f"{hname}_{proc}",
                          len(eta_bins) - 1, array('f', eta_bins),     # pho1_eta axis
                          len(eta_bins) - 1, array('f', eta_bins),     # pho2_eta axis
                          len(mass_bins) - 1 , array('f', mass_bins)            # you choose these bins
                      )

                      tree = root_infiles[proc].Get(f"tagsDumper/trees/{proc}_125_13TeV_{cat}")
                      if not tree:
                          print(f"WARNING: TTree '{cat}' not found.")
                          print(processes[proc], f"tagsDumper/trees/{proc}_125_13TeV_{cat}")
                          continue

                      # Fill histogram
                      tree.Draw(f"CMS_hgg_mass:abs(subleadEta):abs(leadEta)>>{hname}_{proc}", sel, "goff")

                      hist.Add(hist_proc)

                    bins_json = []

                    nx = hist.GetNbinsX()
                    ny = hist.GetNbinsY()

                    # Loop over 2D eta bins (x=eta_sub, y=eta_lead)
                    for ix in range(1, nx+1):
                        for iy in range(1, ny+1):
                            # Project mass along z for this eta bin
                            proj = hist.ProjectionZ(f"proj_{ix}_{iy}", ix, ix, iy, iy)
                            integral = proj.Integral()
                            mass_rms = proj.GetRMS() if integral>10 else -1

                            # Add corrections/systematics


                            corr_lead = corr_map[f"({i_ptL},{i_r9L},{iy-1})"]
                            corr_sub  = corr_map[f"({i_ptS},{i_r9S},{ix-1})"]
                            syst_lead = syst_map[f"({i_ptL},{i_r9L},{iy-1})"]   # relative uncertainty on pT
                            syst_sub  = syst_map[f"({i_ptS},{i_r9S},{ix-1})"]-1

                            # Diphoton mass correction = product of photon corrections
                            correction = corr_lead * corr_sub

                            systematic = ((1+syst_lead)*(1+syst_sub))**0.5 - 1

                            if mass_rms == 0 or integral <= 10:
                              mass_rms = -1
                              integral = 0
                              continue

                            # m_cat0 = sum (m_subset * w_subset) / sum(w_subset)

                            curr_weight = integral/(mass_rms**2)


                            if f"({i_ptL},{i_r9L},{iy-1})" == f"({i_ptS},{i_r9S},{ix-1})":
                              syst_per_bin_cat[cat][f"R9_bin_{i_r9L}"][f"pT_bin_{i_ptL}"][f"eta_bin{iy-1}"] += curr_weight*( ((1+syst_lead)*(1+syst_sub))**0.5 - 1 )
                            else:
                              syst_per_bin_cat[cat][f"R9_bin_{i_r9L}"][f"pT_bin_{i_ptL}"][f"eta_bin{iy-1}"] += curr_weight*( (1+syst_lead)**0.5 - 1 )
                              syst_per_bin_cat[cat][f"R9_bin_{i_r9S}"][f"pT_bin_{i_ptS}"][f"eta_bin{ix-1}"] += curr_weight*( (1+syst_sub)**0.5 - 1 )

                            syst_per_cat_sum += curr_weight*(systematic**2)
                            weight_per_cat_sum += curr_weight

                            output[cat]["mass_res"] += (mass_rms**2)*integral
                            output[cat]["n_ev"] += integral

                            bins_json.append({
                                "eta_sub_bin": (hist.GetXaxis().GetBinLowEdge(ix), hist.GetXaxis().GetBinUpEdge(ix)),
                                "eta_lead_bin": (hist.GetYaxis().GetBinLowEdge(iy), hist.GetYaxis().GetBinUpEdge(iy)),
                                "integral": integral,
                                "fraction": integral/hist_1d.Integral(),
                                "mass_RMS": mass_rms,
                                "correction": correction,
                                "systematic": systematic,
                                "syst_lead": syst_lead,
                                "syst_sub": syst_sub,
                                "contrib_lead": curr_weight*( (1+syst_lead)**0.5 - 1 ),
                                "contrib_sub": curr_weight*( (1+syst_sub)**0.5 - 1 ),
                                "contrib_both_if_matching": curr_weight*( ((1+syst_lead)*(1+syst_sub))**0.5 - 1 )
                            })

                    f.cd()
                    hist.Write()

                    output[cat][tag] = {
                        "bins": bins_json,
                    }

    for r9_bin in range(len(r9_bins)-1):
      for pt_bin in range(len(pt_bins)-1):
        for eta_bin in range(len(eta_bins)-1):
            syst_per_bin_cat[cat][f"R9_bin_{r9_bin}"][f"pT_bin_{pt_bin}"][f"eta_bin{eta_bin}"] /= weight_per_cat_sum
            #this part is hardcoded for now...
            if args.make_comparisons:
              colname = f"MCZmmgScale{['Low', 'High'][r9_bin]}R9{['CentralEB', 'OuterEB', 'EE'][eta_bin]}{['Low', 'High'][pt_bin]}Pt_13TeVscaleCorr_mean"
              current_pickle_impact = pkl[["proc", colname]].copy()

              current_pickle_impact.loc[:, "yield"] = current_pickle_impact["proc"].map(yields_per_process_cat[cat])

              curr_weighted_sum = (current_pickle_impact[colname] * current_pickle_impact["yield"]).sum()
              curr_weight_sum = sum(yields_per_process_cat[cat].values())

              syst_per_bin_cat[cat][f"R9_bin_{r9_bin}"][f"pT_bin_{pt_bin}"][f"eta_bin{eta_bin}_calcPhotonSyst"] = curr_weighted_sum/curr_weight_sum

    output[cat]["syst_per_cat"] = math.sqrt(syst_per_cat_sum/weight_per_cat_sum)
    output[cat]["syst_per_cat_and_bin"] = syst_per_bin_cat[cat]

    output[cat]["mass_res"] = math.sqrt(output[cat]["mass_res"] / output[cat]["n_ev"] )
    output[cat]["S"] = categories[cat]["S"]
    output[cat]["B"] = categories[cat]["B"]
    output[cat]["S_eff"] = output[cat]["S"]/(1 + output[cat]["B"]/output[cat]["S"])
    output[cat]["eff_mass_res"] = output[cat]["mass_res"]/math.sqrt(output[cat]["S_eff"])

f.Close()

# Save JSON
with open("output.json", "w") as fout:
    json.dump(output, fout, indent=2)

print("DONE: all histograms and output.json generated.")

syst_per_bin = {}
weights_per_bin = {}
syst_tot = 0

if args.make_comparisons:
  impact_dct = {
    "POIs": [
      {
        "fit": [
  	-99,
          -99,
          -99
        ],
        "name": "MH"
      }
    ],
    "method": "default",
    "params": []
  }


for i_r9_bin in range(len(r9_bins)-1):
  r9_bin = f"r9_from_{r9_bins[i_r9_bin]}_to_{r9_bins[i_r9_bin+1]}"
  syst_per_bin[r9_bin] = {}
  for i_pt_bin in range(len(pt_bins)-1):
    pt_bin = f"pt_from_{pt_bins[i_pt_bin]}_to_{pt_bins[i_pt_bin+1]}"
    syst_per_bin[r9_bin][pt_bin] = {}
    for i_eta_bin in range(len(eta_bins)-1):
      eta_bin = f"eta_from_{eta_bins[i_eta_bin]}_to_{eta_bins[i_eta_bin+1]}"
      syst_per_bin[r9_bin][pt_bin][eta_bin] = 0
      weight = 0
      for i_cat, cat in enumerate(categories):
        syst_per_bin[r9_bin][pt_bin][eta_bin] += syst_per_bin_cat[cat][f"R9_bin_{i_r9_bin}"][f"pT_bin_{i_pt_bin}"][f"eta_bin{i_eta_bin}"]/(output[cat]["eff_mass_res"])**2
        weight += 1/(output[cat]["eff_mass_res"])**2
      syst_per_bin[r9_bin][pt_bin][eta_bin] /= weight
      syst_per_bin[r9_bin][pt_bin][eta_bin] *= 125e3

      if args.make_comparisons:
         impact_dct["params"].append({
           "name": f"CMS_hgg_nuisance_MCZmmgScale{['Low', 'High'][i_r9_bin]}R9{['CentralEB', 'OuterEB', 'EE'][i_eta_bin]}{['Low', 'High'][i_pt_bin]}Pt_13TeVscaleCorr",
           "fit": [-1, 0, 1], "MH": [125.38-syst_per_bin[r9_bin][pt_bin][eta_bin]*1e-3, 125.38, 125.38+syst_per_bin[r9_bin][pt_bin][eta_bin]*1e-3], "groups": [], "type": "Gaussian",
           "prefit": [-1.0, 0.0, 1.0], "impact_MH": syst_per_bin[r9_bin][pt_bin][eta_bin]*1e-3
         })

      syst_tot += (syst_per_bin[r9_bin][pt_bin][eta_bin])**2

print(f"syst tot: {math.sqrt(syst_tot)}")

syst_per_bin["syst_tot"] = math.sqrt(syst_tot)

with open("output_no_cats.json", "w") as fout:
  json.dump(syst_per_bin, fout, indent=2)

if args.make_comparisons:
  with open("impacts.json", "w") as fout:
    json.dump(impact_dct, fout, indent=2)

