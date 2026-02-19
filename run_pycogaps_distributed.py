# run_pycogaps_distributed.py
# Standalone, portable distributed/multiprocess CoGAPS runner with logging.
# Run from the notebook using:
#   python -u run_pycogaps_distributed.py
#
# IMPORTANT: this script MUST be guarded by __main__ for spawn-based systems (Windows/macOS).

import os
import sys
import time
import json
import logging
from datetime import datetime

import numpy as np
import scanpy as sc
from PyCoGAPS.parameters import CoParams, setParams
from PyCoGAPS.pycogaps_main import CoGAPS

CONFIG = {
    "input_h5ad": "/opt/data/kang_counts_25k.h5ad",   # <- key fix
    "backup_url": "https://figshare.com/ndownloader/files/34464122",  # keep as fallback
    "min_cells": 3,
    "target_sum": 1e4,
    "n_top_genes": 3000,
    "hvg_flavor": "seurat_v3",
    "nPatterns": 8,
    "nIterations": 20000,
    "seed": 42,
    "useSparseOptimization": True,
    "distributed": "genome-wide",
    "output_h5ad": "data/cogaps_result_distributed.h5ad",
    "log_dir": "logs",
}

def setup_logger():
    os.makedirs(CONFIG["log_dir"], exist_ok=True)
    os.makedirs("data", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(CONFIG["log_dir"], f"pycogaps_distributed_{ts}.log")

    logger = logging.getLogger("pycogaps_distributed")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")

    # Console (for notebook streaming)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)

    # File
    fh = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)

    logger.info(f"Log file: {log_path}")
    logger.info("CONFIG:")
    logger.info(json.dumps(CONFIG, indent=2))
    return logger

def main():
    logger = setup_logger()

    path = CONFIG["input_h5ad"]
    if os.path.exists(path):
        logger.info(f"Loading local: {path}")
        adata = sc.read_h5ad(path)
    else:
        logger.info(f"Downloading via backup_url to: {path}")
        adata = sc.read(path, backup_url=CONFIG["backup_url"])

    # Preprocess
    adata.layers["counts"] = adata.X.copy()
    sc.pp.filter_genes(adata, min_cells=int(CONFIG["min_cells"]))
    sc.pp.normalize_total(adata, target_sum=float(CONFIG["target_sum"]))
    sc.pp.log1p(adata)

    # HVGs on raw counts layer
    sc.pp.highly_variable_genes(
        adata,
        n_top_genes=int(CONFIG["n_top_genes"]),
        flavor=str(CONFIG["hvg_flavor"]),
        layer="counts",
    )
    adata = adata[:, adata.var["highly_variable"]].copy()
    logger.info(f"After HVGs: {adata}")

    # Prepare genes x cells
    adata_cogaps = adata.T.copy()
    adata_cogaps.X = np.asarray(adata_cogaps.X.toarray(), dtype=np.float64)
    logger.info(f"CoGAPS input: {adata_cogaps} dtype={adata_cogaps.X.dtype}")

    params = CoParams(adata=adata_cogaps)
    setParams(params, {
        "nPatterns": int(CONFIG["nPatterns"]),
        "nIterations": int(CONFIG["nIterations"]),
        "seed": int(CONFIG["seed"]),
        "useSparseOptimization": bool(CONFIG["useSparseOptimization"]),
        "distributed": CONFIG["distributed"],
    })

    logger.info("Starting CoGAPS (distributed)...")
    start = time.time()
    result = CoGAPS(adata_cogaps, params)
    logger.info(f"Finished in {(time.time()-start)/60:.2f} minutes")

    result.write_h5ad(CONFIG["output_h5ad"])
    logger.info(f"Saved: {CONFIG['output_h5ad']}")

if __name__ == "__main__":
    main()
