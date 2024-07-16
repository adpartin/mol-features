import os
from pathlib import Path
import pandas as pd

filepath = Path(__file__).parent
print(filepath)

datadir = filepath / 'data/ovarian/'

outdir = filepath / 'out.ovarian_drug_fea_data'
os.makedirs(outdir, exist_ok=True)

id_name = 'improve_chem_id'
mordred_prefix = 'mordred.'
fps_prefix = 'ecfp4.'

# Load Ovarian drugs
ov_drugs = pd.read_csv(datadir / 'Drugs_For_OV_Proposal_Analysis.txt', sep='\t')
ov_drugs = ov_drugs.sort_values(by='drug_name')

# Remove Cisplatin duplicate (remove Drug_18, keep Drug_42)
ov_drugs = ov_drugs[ov_drugs[id_name] != 'Drug_18']

# Load csa benchmark feature data
# info = pd.read_csv(datadir / 'drug_info.tsv', sep='\t')
info = pd.read_csv(datadir / 'csa_data/raw_data/x_data' / 'drug_info.tsv', sep='\t')
mrd = pd.read_csv(datadir / 'csa_data/raw_data/x_data' / 'drug_mordred.tsv', sep='\t')
fps = pd.read_csv(datadir / 'csa_data/raw_data/x_data' / 'drug_ecfp4_nbits512.tsv', sep='\t')

# Merge ovarian drugs with csa benchmark feature data
mrd_merged = pd.merge(ov_drugs, mrd, on='improve_chem_id')
fps_merged = pd.merge(ov_drugs, fps, on='improve_chem_id')
info_merged = pd.merge(ov_drugs, info, on='improve_chem_id')

# Relevant columns
mrd_cols = [c for c in mrd_merged.columns if mordred_prefix in c]
fps_cols = [c for c in fps_merged.columns if fps_prefix in c]
mrd_merged = mrd_merged[[id_name] + mrd_cols]
fps_merged = fps_merged[[id_name] + fps_cols]

# print(mrd_merged.shape)
# print(fps_merged.shape)
# print(info_merged.shape)

# print(mrd_merged.iloc[:10, :10])
# print(fps_merged.iloc[:10, :10])
# print(info_merged.iloc[:10])

# Remove SMILES duplicates
smi = info_merged.drop_duplicates(subset=['drug_name', id_name, 'canSMILES'])
print(smi.shape)
print(smi.iloc[:, :8])

# Remove NSC duplicates (keep CTRP, GDSC, etc. instead)
dups = smi[smi.duplicated(subset=['drug_name', id_name], keep=False)]
dups_nsc = dups[[True if 'NSC' in i else False for i in dups['DrugID']]]
dups_nsc_list = dups_nsc['DrugID'].values
# print(smi.shape)
smi = smi[~smi['DrugID'].isin(dups_nsc_list)]
# print(smi.shape)
# print(smi.iloc[:, :8])
smi = smi[[id_name, 'canSMILES']]

# Save data
mrd_merged.to_csv(outdir / 'drug_mordred_ovarian.tsv', sep='\t', index=False)
fps_merged.to_csv(outdir / 'drug_ecfp4_nbits512_ovarian.tsv', sep='\t', index=False)
info_merged.to_csv(outdir / 'drug_info_ovarian.tsv', sep='\t', index=False)
smi.to_csv(outdir / 'drug_SMILES_ovarian.tsv', sep='\t', index=False)

print("\nMordred:\n", mrd_merged.iloc[:4, :10])
print("\nECFP4:\n", fps_merged.iloc[:4, :10])
print("\nInfo:\n", info_merged.iloc[:4])
print("\nSMILES:\n", smi) # .iloc[:4])

print("Finished.")
