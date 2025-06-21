#/bin/bash
conda create -y -n lapesp python=3.10 --solver classic
conda activate lapesp
conda install ffmpeg -c conda-forge --solver classic
pip install -e lerobot/