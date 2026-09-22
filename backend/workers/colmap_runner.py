"""
colmap_runner.py

Wraps the COLMAP CLI to turn a folder of frames into a sparse 3D reconstruction.

Pipeline: feature_extractor -> exhaustive_matcher -> mapper
Output: a "sparse/0" folder containing cameras.bin, images.bin, points3D.bin
        (this is what Nerfstudio/Splatfacto reads in Week 2 step 2)

Windows note: COLMAP must be installed and on PATH, OR set COLMAP_EXE below to
the full path of COLMAP.bat / colmap.exe from the Windows release zip.
Download: https://github.com/colmap/colmap/releases (grab the Windows build)
"""

import os
import subprocess
import time

# If "colmap" isn't on PATH, point this at your COLMAP.bat, e.g.:
COLMAP_EXE = r"C:\colmap-x64-windows-nocuda\COLMAP.bat"


class ColmapError(Exception):
    pass


def _run(cmd: list[str], step_name: str, log_file):
    """Run a subprocess command, streaming output to a log file. Raises on failure."""
    log_file.write(f"\n=== {step_name} ===\n$ {' '.join(cmd)}\n")
    log_file.flush()

    result = subprocess.run(
        cmd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if result.returncode != 0:
        raise ColmapError(
            f"COLMAP step '{step_name}' failed with exit code {result.returncode}. "
            f"Check the log for details."
        )


def run_colmap(scan_id: str, images_dir: str, output_dir: str) -> str:
    """
    Runs the full COLMAP sparse reconstruction pipeline on a folder of images.

    Args:
        scan_id: the scan's UUID (used for logging only)
        images_dir: folder containing frame_0000.jpg, frame_0001.jpg, ...
        output_dir: folder to write colmap outputs into
                    (a "database.db" file and a "sparse/" folder will be created here)

    Returns:
        path to the sparse model folder (output_dir/sparse/0), which is what
        splatfacto_runner.py needs next.

    Raises:
        ColmapError if any COLMAP step fails.
    """
    os.makedirs(output_dir, exist_ok=True)
    db_path = os.path.join(output_dir, "database.db")
    sparse_dir = os.path.join(output_dir, "sparse")
    os.makedirs(sparse_dir, exist_ok=True)

    log_path = os.path.join(output_dir, "colmap.log")
    start = time.time()

    with open(log_path, "a") as log:
        log.write(f"\n\n########## COLMAP run for scan {scan_id} ##########\n")

        # Step 1: extract SIFT features from every image
        _run(
            [
                COLMAP_EXE, "feature_extractor",
                "--database_path", db_path,
                "--image_path", images_dir,
                "--ImageReader.single_camera", "1",  # all frames from same headset camera
            ],
            "feature_extractor",
            log,
        )

        # Step 2: match features across all image pairs
        # (exhaustive_matcher is correct for <~500 images; if you have more,
        #  switch to sequential_matcher since Quest frames are captured in order)
        _run(
            [
                COLMAP_EXE, "exhaustive_matcher",
                "--database_path", db_path,
            ],
            "exhaustive_matcher",
            log,
        )

        # Step 3: incremental structure-from-motion -> sparse point cloud + camera poses
        _run(
            [
                COLMAP_EXE, "mapper",
                "--database_path", db_path,
                "--image_path", images_dir,
                "--output_path", sparse_dir,
            ],
            "mapper",
            log,
        )

        elapsed = time.time() - start
        log.write(f"\nCOLMAP finished in {elapsed:.1f} seconds\n")

    model_dir = os.path.join(sparse_dir, "0")
    if not os.path.isdir(model_dir):
        raise ColmapError(
            f"COLMAP ran but produced no model at {model_dir}. "
            "This usually means not enough image overlap/features were found — "
            "check colmap.log and try scanning with more overlap between frames."
        )

    return model_dir


if __name__ == "__main__":
    # Quick manual test:
    #   python colmap_runner.py <path_to_images_folder> <path_to_output_folder>
    import sys

    if len(sys.argv) != 3:
        print("Usage: python colmap_runner.py <images_dir> <output_dir>")
        sys.exit(1)

    images_dir, output_dir = sys.argv[1], sys.argv[2]
    print(f"Running COLMAP on {images_dir} -> {output_dir} ...")
    model_path = run_colmap("manual-test", images_dir, output_dir)
    print(f"Done. Sparse model at: {model_path}")