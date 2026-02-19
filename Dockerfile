FROM jhudsl/ottr_ocs_py:dev

USER root

# -----------------------------------------------------------------------------
# Why this Dockerfile exists
# -----------------------------------------------------------------------------
# - Provides RStudio Server + Quarto via the OTTR base image
# - Adds system build deps needed to create a venv and compile PyCoGAPS/CoGAPS
# - Bakes the Quarto project files into the image
# - DOES NOT download the dataset during build (Figshare downloads may be blocked
#   by AWS WAF for non-browser clients).
#
# Dataset is expected to be mounted at:
#   /opt/data/kang_counts_25k.h5ad
# -----------------------------------------------------------------------------

# Base image includes a Vivaldi apt repo entry without a signing key; remove it so apt works.
RUN rm -f /etc/apt/sources.list.d/vivaldi.list /etc/apt/sources.list.d/vivaldi*.list || true

# System deps needed for: python -m venv, building PyCoGAPS/CoGAPS core, cloning repos
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-venv \
    build-essential \
    git \
    libboost-all-dev \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Create a mount point for the dataset (users will mount a host folder here)
RUN mkdir -p /opt/data && chmod 755 /opt/data

# ---- Bake the Quarto project into the image ----
WORKDIR /home/rstudio/project
COPY _environment* ./
COPY _quarto.yml ./
COPY README.md ./
COPY requirements.txt ./
COPY setup_venv.sh ./
COPY run_pycogaps_distributed.py ./
COPY *.qmd ./

# Ensure rstudio user can write in the project directory
RUN chown -R rstudio:rstudio /home/rstudio/project

# IMPORTANT: do NOT switch to USER rstudio here.
# The base image startup (s6) expects to run as root.
