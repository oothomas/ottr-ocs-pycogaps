# CoGAPS Case Study 4 — Docker + Quarto + PyCoGAPS (Student/Instructor)

This repo provides a reproducible environment for **Case Study 4** using:

- **Docker** (RStudio Server + Quarto)
- A project-local Python environment (`.venv`)
- **PyCoGAPS built from source** (includes the C++ CoGAPS core)

## Dataset strategy (Option A: user-provided mount)

Figshare downloads can be blocked by AWS WAF (you may see `x-amzn-waf-action: challenge` / empty downloads).
So this project assumes **you download the dataset once via your browser** and mount it into the container.

The notebook expects the dataset at:

- `/opt/data/kang_counts_25k.h5ad`

---

## 1) Download the dataset (one-time)

Download the file from Figshare (use a web browser if curl fails):

- https://figshare.com/ndownloader/files/34464122

Save it as:

- `kang_counts_25k.h5ad`

Create a local folder (in the repo root) and place the file there:

```bash
mkdir -p data_mount
# move or save the downloaded file here:
# data_mount/kang_counts_25k.h5ad
```

---

## 2) Build the Docker image

From the repo root (where the Dockerfile is):

```bash
docker build --platform linux/amd64 -t cogaps-case-study4:dev .
```

> Apple Silicon Macs: the `--platform linux/amd64` flag is required.

---

## 3) Run RStudio Server (recommended: mount repo + dataset)

This run command mounts:
- your local repo → `/home/rstudio/project` (so edits + renders persist on your machine)
- your dataset folder → `/opt/data` (read-only)

```bash
docker run --platform linux/amd64 -it --rm \
  -p 8787:8787 \
  -e PASSWORD="Password12" \
  -v "$PWD":/home/rstudio/project \
  -w /home/rstudio/project \
  -v "$PWD/data_mount":/opt/data:ro \
  cogaps-case-study4:dev
```

Open:
- http://localhost:8787
- User: `rstudio`
- Password: `Password12` (or whatever you set)

---

## 4) One-time setup inside the container

In **RStudio → Terminal**:

```bash
cd /home/rstudio/project
bash setup_venv.sh
```

(Optional sanity check)

```bash
source _environment
quarto check jupyter
```

---

## 5) Run the case study

### Interactive mode (recommended for students)
Open the `.qmd` file in RStudio and run chunks one by one:

- `cogaps_case_study4_student.qmd` (render-safe version recommended)

### Render mode (HTML report)
```bash
cd /home/rstudio/project
source _environment
quarto render cogaps_case_study4_student.qmd
```

---

## Optional: Distributed CoGAPS (advanced)

Run distributed CoGAPS as a **standalone script** (not during Quarto render):

```bash
cd /home/rstudio/project
source _environment
./.venv/bin/python run_pycogaps_distributed.py
```

This should write:
- `data/cogaps_result_distributed.h5ad`

---

## Repo hygiene / what not to commit

Do **not** commit:
- `.venv/`
- `vendor/`
- `data/` outputs
- `logs/`
- `*.h5ad` datasets

(See `.gitignore`.)
