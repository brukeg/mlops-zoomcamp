# Conda Environment Setup in GitHub Codespaces

## One-Time Setup

Install Miniconda (skip if already installed):

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

Follow the prompts, accept defaults, and say **yes** when it asks to initialize conda. Then reload your shell:

```bash
source ~/.bashrc
```

Create the `mlops` environment:

```bash
conda create -n mlops python=3.12 pandas pyarrow scikit-learn jupyter -y
```

## Every Time You Open the Codespace

Activate the environment:

```bash
conda activate mlops
```

Navigate to your working directory and start Jupyter:

```bash
cd 01-intro
jupyter notebook --no-browser
```

Codespaces will detect the port and show a popup to open it in your browser. Click it.

## Installing New Packages

Always make sure you're in the `mlops` environment first:

```bash
conda activate mlops
conda install <package-name>
```

If a package isn't available via conda, use pip:

```bash
pip install <package-name>
```

## Verifying You're in the Right Environment

Your terminal prompt should show `(mlops)`, not `(base)`:

```
(mlops) @brukeg ➜ /workspaces/mlops-zoomcamp $   ← correct
(base) @brukeg ➜ /workspaces/mlops-zoomcamp $    ← wrong
```

In a Jupyter notebook, verify with:

```python
import sys
print(sys.executable)
# Should show: /home/codespace/miniconda3/envs/mlops/bin/python
```

## Troubleshooting

**Notebook can't find a package you just installed:**
You probably installed it in `base` instead of `mlops`. Activate `mlops`, install again, and restart the Jupyter kernel.

**Jupyter kernel doesn't show the `mlops` environment:**
```bash
conda activate mlops
python -m ipykernel install --user --name mlops --display-name "Python (mlops)"
```

**Codespace restarted and conda isn't recognized:**
```bash
source ~/.bashrc
```