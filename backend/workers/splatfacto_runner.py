"""
splatfacto_runner.py

Wraps Nerfstudio's `ns-train splatfacto` to train a Gaussian Splat model
from a COLMAP sparse reconstruction, then exports it to a .splat file.

IMPORTANT (read this before running):
This step needs a CUDA GPU. It will not run in any reasonable time on a
CPU-only Windows machine. Write/test this code now, but the *actual* training
run should happen on the AWS g4dn.xlarge box in Week 3.

Install (on the GPU machine, Linux or WSL2 recommended):
    pip install nerfstudio
    docs: https://docs.nerf.studio/quickstart/installation.html
"""

import os
import shutil
import subprocess
import time

# Nerfstudio lives in its own venv (nerfstudio_venv, Python 3.10). We launch it
# through that venv's python.exe with "-m" instead of the ns-train.exe wrapper,
# which avoids PATH problems and Windows Device Guard blocking .exe launchers.
# Adjust this path if your project folder moves.
NERFSTUDIO_VENV_SCRIPTS = r"R:\Immverse\Hyperscape\metaOS_APK\backend\nerfstudio_venv\Scripts"
NS_PYTHON = os.path.join(NERFSTUDIO_VENV_SCRIPTS, "python.exe")
NS_TRAIN_CMD = [NS_PYTHON, "-m", "nerfstudio.scripts.train"]
NS_EXPORT_CMD = [NS_PYTHON, "-m", "nerfstudio.scripts.exporter"]


class SplatfactoError(Exception):
    pass


def _run(cmd: list[str], step_name: str, log_file):
    log_file.write(f"\n=== {step_name} ===\n$ {' '.join(cmd)}\n")
    log_file.flush()

    # Force UTF-8 so Nerfstudio's rich console (box-drawing characters) can
    # write into the log file on Windows instead of crashing on cp1252.
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    result = subprocess.run(
        cmd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,  # never wait on an interactive prompt
        text=True,
        env=env,
    )

    if result.returncode != 0:
        raise SplatfactoError(
            f"Step '{step_name}' failed with exit code {result.returncode}. "
            f"Check the log for details."
        )


def run_splatfacto(
    scan_id: str,
    images_dir: str,
    colmap_model_dir: str,
    output_dir: str,
    max_train_steps: int = 15000,
) -> str:
    """
    Trains a Gaussian Splat model from a COLMAP reconstruction and exports it.

    Args:
        scan_id: scan UUID (used for the Nerfstudio experiment name)
        images_dir: same folder of frames used for COLMAP
        colmap_model_dir: path to the sparse/0 folder from colmap_runner.run_colmap()
        output_dir: where to write nerfstudio's training output + final .splat file
        max_train_steps: fewer steps = faster but lower quality. 15000 is a
            reasonable MVP default; drop to ~7000 if you need faster iteration.

    Returns:
        path to the exported .splat file.

    Raises:
        SplatfactoError if training or export fails.
    """
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "splatfacto.log")
    start = time.time()

    # Nerfstudio's colmap dataparser expects a specific folder layout:
    #   <data_dir>/images/         <- the frames
    #   <data_dir>/colmap/sparse/0 <- the colmap model
    data_dir = os.path.join(output_dir, "ns_data")
    ns_images_dir = os.path.join(data_dir, "images")
    ns_colmap_dir = os.path.join(data_dir, "colmap", "sparse", "0")

    os.makedirs(ns_images_dir, exist_ok=True)
    os.makedirs(ns_colmap_dir, exist_ok=True)

    # Symlink/copy frames and colmap model into the layout nerfstudio expects
    for fname in os.listdir(images_dir):
        src = os.path.join(images_dir, fname)
        dst = os.path.join(ns_images_dir, fname)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)

    for fname in os.listdir(colmap_model_dir):
        src = os.path.join(colmap_model_dir, fname)
        dst = os.path.join(ns_colmap_dir, fname)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)

    experiment_name = f"scan_{scan_id}"

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n\n########## Splatfacto run for scan {scan_id} ##########\n")

        # Step 1: train
        _run(
            [
                *NS_TRAIN_CMD, "splatfacto",
                "--data", data_dir,
                "--output-dir", output_dir,
                "--experiment-name", experiment_name,
                "--max-num-iterations", str(max_train_steps),
                "--viewer.quit-on-train-completion", "True",
                "colmap",  # dataparser: tells nerfstudio the data came from colmap
                # Use full-res frames as-is. Without this, nerfstudio stops and
                # asks an interactive "downscale images? [y/n]" question that a
                # background worker can never answer.
                "--downscale-factor", "1",
            ],
            "ns-train splatfacto",
            log,
        )

        # Nerfstudio nests output as: <output_dir>/<experiment_name>/splatfacto/<timestamp>/
        exp_dir = os.path.join(output_dir, experiment_name, "splatfacto")
        run_dirs = sorted(os.listdir(exp_dir))
        if not run_dirs:
            raise SplatfactoError(f"No training run found under {exp_dir}")
        latest_run = os.path.join(exp_dir, run_dirs[-1])
        config_path = os.path.join(latest_run, "config.yml")

        # Step 2: export the trained model to a portable .splat file
        splat_output_dir = os.path.join(output_dir, "export")
        os.makedirs(splat_output_dir, exist_ok=True)

        _run(
            [
                *NS_EXPORT_CMD, "gaussian-splat",
                "--load-config", config_path,
                "--output-dir", splat_output_dir,
            ],
            "ns-export gaussian-splat",
            log,
        )

        elapsed = time.time() - start
        log.write(f"\nSplatfacto finished in {elapsed:.1f} seconds\n")

    splat_file = os.path.join(splat_output_dir, "splat.ply")
    if not os.path.isfile(splat_file):
        raise SplatfactoError(
            f"Export ran but no splat.ply found at {splat_file}. Check splatfacto.log."
        )

    return splat_file


if __name__ == "__main__":
    # Quick manual test:
    #   python splatfacto_runner.py <images_dir> <colmap_model_dir> <output_dir>
    import sys

    if len(sys.argv) != 4:
        print("Usage: python splatfacto_runner.py <images_dir> <colmap_model_dir> <output_dir>")
        sys.exit(1)

    images_dir, colmap_dir, output_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    print("Training splatfacto (this needs a CUDA GPU) ...")
    splat_path = run_splatfacto("manual-test", images_dir, colmap_dir, output_dir)
    print(f"Done. Splat file at: {splat_path}")
    