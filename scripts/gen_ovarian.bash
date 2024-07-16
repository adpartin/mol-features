#!/bin/bash

# Generate molecular features for Pilot1.
# par_jobs=1
par_jobs=32
# par_jobs=64
# fea_type="descriptors fps"
fea_type="mordred fps"
# fea_type="mordred"
nbits=512

# -------------------------------------------------------
# 1800 drugs (CCLE, CTRP, gCSI, GDSC, NCI60): 2142 smiles

# Pilot1
# dname=Pilot1/July2020/drug_info
# gout=out.pilot1/July2020/drug_info

# IMPROVE
# FNAME=drug_info_2k  # legacy
# FNAME=drug_info.tsv
# FNAME=OvarianCancerDrugsIMPROVE.txt
# FNAME=drug_SMILES.tsv
FNAME=PDO_pubchem_smiles.tsv
dname=ovarian/${FNAME}
gout=out.ovarian/${FNAME}

smiles_path=data/$dname

id_name=improve_chem_id

python src/gen_mol_fea.py \
    --smiles_path $smiles_path \
    --id_name $id_name \
    --nbits $nbits \
    --gout $gout \
    --par_jobs $par_jobs \
    --ignore_3D \
    --fea_type $fea_type
