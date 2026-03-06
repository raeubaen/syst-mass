import json
import sys

l = json.load(open(sys.argv[1]))

cats = l.keys()

for cat in cats:
  d = l[cat]["syst_per_cat_and_bin"]
  s = 0
  for k1 in d:
    for k2 in d[k1]:
      for k3 in d[k1][k2]:
        s += d[k1][k2][k3]
  print(cat, f"{s*125e3} MeV")
