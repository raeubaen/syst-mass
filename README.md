**Nuisances "bins"**:
- HighR9CentralEBHighPt
- HighR9CentralEBLowPt
- HighR9CentralEBMedPt
- HighR9EEHighPt
- HighR9EELowPt
- HighR9EEMedPt
- HighR9OuterEBHighPt
- HighR9OuterEBLowPt
- HighR9OuterEBMedPt
- LowR9CentralEBHighPt
- LowR9CentralEBLowPt
- LowR9CentralEBMedPt
- LowR9EEHighPt
- LowR9EELowPt
- LowR9EEMedPt
- LowR9OuterEBHighPt
- LowR9OuterEBLowPt
- LowR9OuterEBMedPt

**Bins**:
- **CentralEB:** \(|\eta| \in [0, 1]\)  
- **OuterEB:** \(|\eta| \in [1, 1.5]\)  
- **EE:** \(|\eta| \in [1, 1.5]\)

- **HighR9:** \(R9 > 0.96\)  
- **LowR9:** \(R9 < 0.96\)

- **Low \(p_T\):** \(p_T \in [25, 45]\)  
- **Medium \(p_T\):** \(p_T \in [45, 80]\)  
- **High \(p_T\):** \(p_T \in [80, +\infty]\)

**To get the nuisances bins**:
- start from a flashgg output file:
'''bash
root output_ggh_125.root -e "tagsDumper->cd(); trees->cd(); gDirectory->ls(); exit(0);" | grep "MCZmmgScale" | grep "Up01sigma" | awk -F "MCZmmgScale" '{print $2}' | awk -F "Up01sigma;1" '{print $1}' | sort | uniq
'''

**To get the categories**:
'''bash
root output_ggh_125.root -e "tagsDumper->cd(); trees->cd(); gDirectory->ls(); exit(0);" | grep "MCZmmgScale" | grep "Up01sigma" | awk -F "TeV_" '{print $2}' | awk -F "_MCZmmgScale" '{print $1}' | sort | uniq
'''
# syst-mass
