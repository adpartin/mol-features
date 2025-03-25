#!/bin/bash

# Generate molecular features for Pilot1.
# par_jobs=1
par_jobs=16
# par_jobs=32
# par_jobs=64
fea_type="mordred"
# fea_type="mordred fps"
# nbits=512

# -------------------------------------------------------
# 1800 drugs (CCLE, CTRP, gCSI, GDSC, NCI60): 2142 smiles

# IMPROVE
# dname=improve/benchmark_drug_SMILES.tsv
dname=improve/drug_SMILES.tsv
gout=out.improve/benchmark

smiles_path=data/$dname

# id_name=ID
id_name=improve_chem_id

python src/gen_mol_fea.py \
    --smiles_path $smiles_path \
    --id_name $id_name \
    --gout $gout \
    --par_jobs $par_jobs \
    --ignore_3D \
    --fea_type $fea_type
