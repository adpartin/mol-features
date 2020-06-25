"""
This script computes molecular features and saves in appropriate files.
The feature columns are prefixed with appropriate string:
    - Mordred descriptors (dd_)
    - ECFP2 (ecfp2_)
    - ECFP4 (ecfp4_)
    - ECFP6 (ecfp6_)
    - Images (stored in dict)
"""
import warnings
warnings.filterwarnings('ignore')

import os
import sys
from pathlib import Path
from time import time
from datetime import datetime
import argparse
from pprint import pformat
import pickle

import numpy as np
import pandas as pd

filepath = Path(__file__).resolve().parent

# Utils
# sys.path.append( os.path.abspath(filepath/'../utils') )
from utils.classlogger import Logger
from utils.utils import load_data, get_print_func, drop_dup_rows, dropna
from utils.smiles import canon_smiles, smiles_to_mordred, smiles_to_fps, smiles_to_images

# Date
t = datetime.now()
t = [t.year, '-', t.month, '-', t.day]
date = ''.join( [str(i) for i in t] )

# SMILES_PATH
# SMILES_PATH = Path(filepath, '../data/raw/UC-molecules/UC.smi')
# SMILES_PATH = Path(filepath, '../data/raw/Baseline-Screen-Datasets/BL1(ena+db)/ena+db.smi')
# SMILES_PATH = Path(filepath, '../data/raw/Baseline-Screen-Datasets/BL2-current/BL2.smi').resolve()
SMILES_PATH = Path(filepath, '../sample_data/BL2.smi.sample').resolve()

# Global outdir
OUTDIR = Path(filepath, '../out').resolve()


def parse_args(args):
    parser = argparse.ArgumentParser(description='Generate molecular feature sets.')
    parser.add_argument('--smiles_path',
                        type=str,
                        default=SMILES_PATH,
                        help=f'Full path to the smiles file (default: {SMILES_PATH}).')
    parser.add_argument('-od', '--outdir',
                        type=str,
                        default=OUTDIR,
                        help=f'Output dir (default: {OUTDIR}).')
    parser.add_argument('--par_jobs',
                        type=int, 
                        default=1,
                        help=f'Number of joblib parallel jobs (default: 1).')
    parser.add_argument('--i1',
                        type=int, 
                        default=0,
                        help=f'Start index of a smiles sample (default: 0).')
    parser.add_argument('--i2',
                        type=int, 
                        default=None,
                        help=f'End index of smiles sample (default: None).')
    args, other_args = parser.parse_known_args(args)
    return args


def add_fea_prfx(df, prfx:str, id0:int):
    """ Add prefix feature columns. """
    return df.rename(columns={s: prfx+str(s) for s in df.columns[id0:]})


def get_image(mol):
    image = (255 * transforms.ToTensor()(Invert()(generateFeatures.smiles_to_image(mol))).numpy()).astype(np.uint8)
    return image

# def get_image(mol):
#     """ (AP) breakdown of the function. """
#     im = generateFeatures.smiles_to_image(mol)
#     im = Invert()(im)
#     im = transforms.ToTensor()(im)
#     im = im.numpy()
#     im = 255 * im
#     image = im.astype(np.uint8)
#     return image


def run(args):
    import ipdb; ipdb.set_trace()
    t0 = time()
    smiles_path = args['smiles_path']
    par_jobs = args['par_jobs']
    
    print('\nLoad SMILES ...')
    smiles_path = Path(args['smiles_path'])
    # smi = pd.read_csv( smiles_path, sep='\t', names=['SMILES', 'TITLE'] )
    smi = pd.read_csv( smiles_path )
    smi = smi.astype({'SMILES': str, 'TITLE': str})
    smi['SMILES'] = smi['SMILES'].map(lambda x: x.strip())
    smi['TITLE'] = smi['TITLE'].map(lambda x: x.strip())
    n_smiles = smi.shape[0]
    fea_id0 = smi.shape[1] # this used as index where features begin

    # Create outdir
    i1, i2 = args['i1'], args['i2']
    ids_dir = 'smi.ids.{}-{}'.format(i1, i2)
    if i2 is None:
        i2 = n_smiles
    # outdir = Path(args['outdir'])/date/ids_dir
    outdir = Path(args['outdir'])/ids_dir
    os.makedirs( outdir, exist_ok=True )

    # Logger
    lg = Logger( outdir/'gen.fea.dfs.log' )
    print_fn = get_print_func( lg.logger )
    print_fn( f'File path: {filepath}' )
    print_fn( f'\n{pformat(args)}' )

    print_fn('\nInput data path  {}'.format( smiles_path ))
    print_fn('Output data dir  {}'.format( outdir ))

    # Duplicates
    # dup = smi[ smi.duplicated(subset=['smiles'], keep=False) ].reset_index(drop=True)
    # print( dup['smiles'].value_counts() )

    # Drop duplicates
    smi = drop_dup_rows(smi, print_fn)
    
    # Exract subset SMILES
    smi = smi.iloc[i1:i2+1, :].reset_index(drop=True)

    print_fn('\nCanonicalize SMILES ...')
    can_smi_vec = canon_smiles( smi['SMILES'], par_jobs=par_jobs )
    can_smi_vec = pd.Series(can_smi_vec)

    # Save bad SMILES to file (that were not canonicalized)
    nan_ids = can_smi_vec.isna()
    bad_smi = smi[ nan_ids ]
    if len(bad_smi) > 0:
        bad_smi.to_csv(outdir/'smi_canon_err.csv', index=False)

    # Keep the good (canonicalized) SMILES
    smi['SMILES'] = can_smi_vec
    smi = smi[ ~nan_ids ].reset_index(drop=True)


    # ========================================================
    # Generate imgaes
    # --------------------------
    images = smiles_to_images(smi, smi_col_name='SMILES', title_col_name='TITLE',
            molSize=(128, 128), kekulize=True, par_jobs=par_jobs)
    # print(images[0].keys())
    img_outpath = outdir/f'images.ids.{i1}-{i2}.pkl'

    # Dump images to file (list of dicts)
    pickle.dump( images, open(img_outpath, 'wb') )
    # Load pkl
    # aa = pickle.load(open(img_outpath, 'rb'))
    # sum(images[0]['img'].reshape(-1,)-aa[0]['img'].reshape(-1,))


    # ========================================================
    # Generate fingerprints
    # --------------------------
    def gen_fps_and_save(smi, radius=1, par_jobs=par_jobs):
        file_format = 'parquet'
        ecfp = smiles_to_fps(smi, smi_name='SMILES', radius=radius, par_jobs=par_jobs)
        ecfp = add_fea_prfx(ecfp, prfx=f'ecfp{2*radius}.', id0=fea_id0)
        ecfp.to_parquet( outdir/f'ecfp{2*radius}.ids.{i1}-{i2}.{file_format}' )
        del ecfp

    gen_fps_and_save(smi, radius=1, par_jobs=par_jobs)
    gen_fps_and_save(smi, radius=2, par_jobs=par_jobs)
    gen_fps_and_save(smi, radius=3, par_jobs=par_jobs)


    # ========================================================
    # Generate descriptors
    # --------------------------
    dd = smiles_to_mordred(smi, smi_name='SMILES', par_jobs=par_jobs)
    dd = add_fea_prfx(dd, prfx='dd_', id0=fea_id0)

    # Filter NaNs (step 1)
    # Drop rows where all values are NaNs
    print_fn('\nDrop rows where all values are NaN ...')
    print_fn('Shape: {}'.format( dd.shape ))
    idx = ( dd.isna().sum(axis=1) == dd.shape[1] ).values
    dd = dd.iloc[~idx, :].reset_index(drop=True)
    # Drop cols where all values are NaNs
    # idx = ( dd.isna().sum(axis=0) == dd.shape[0] ).values
    # dd = dd.iloc[:, ~idx].reset_index(drop=True)
    print_fn('Shape: {}'.format( dd.shape ))

    # Filter NaNs (step 2)
    # Drop rows and cols based on a thershold of NaN values
    # print(dd.isna().sum(axis=1).sort_values(ascending=False))
    # p=dd.isna().sum(axis=1).sort_values(ascending=False).hist(bins=100);
    th = 0.2
    print_fn('\nDrop rows with at least {} NaNs (at least {} out of {}).'.format(
        th, int(th * dd.shape[1]), dd.shape[1]))
    print_fn('Shape: {}'.format( dd.shape ))
    dd = dropna(dd, axis=1, th=th)
    print_fn('Shape: {}'.format( dd.shape ))

    # Cast features (descriptors)
    print_fn('\nCast descriptors to float ...')
    dd = dd.astype({c: np.float32 for c in dd.columns[fea_id0:]})

    # Impute missing values
    print_fn('\nImpute NaNs ...')
    print_fn('Total NaNs: {}'.format( dd.isna().values.flatten().sum() ))
    dd = dd.fillna(0.0)
    print_fn('Total NaNs: {}'.format( dd.isna().values.flatten().sum() ))

    # Save
    print_fn('\nSave ...')
    dd = dd.reset_index(drop=True)
    file_format = 'parquet'
    dd.to_parquet( outdir/'dd.ids.{}-{}.{}'.format(i1, i2, file_format) )
    # dd.to_csv( outdir/'dd.ids.{}-{}.{}'.format(i1, i2, file_format), index=False )


    # ========================================================
    print_fn('\nRuntime {:.2f} mins'.format( (time()-t0)/60 ))
    print_fn('Done.')
    lg.kill_logger()
    
    
def main(args):
    args = parse_args(args)
    args = vars(args)
    run(args)


if __name__ == '__main__':
    main(sys.argv[1:])


