#!/bin/bash

# That's the general workflow to generate molecular features for a relatively
# small set of smiles strings. For the larger set of smiles we can use Parsl.

par_jobs=16
# fea_type="mordred"
fea_type="mordred fps"
nbits=512

dname=tom_2025_06_24/drugs_2025_06_24.tsv
gout=out.tom_2025_06_24

smiles_path=data/$dname

id_name=ID

python src/gen_mol_fea.py \
    --smiles_path $smiles_path \
    --id_name $id_name \
    --nbits $nbits \
    --gout $gout \
    --par_jobs $par_jobs \
    --ignore_3D \
    --fea_type $fea_type
