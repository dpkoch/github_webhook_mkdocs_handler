"""Job to build a mkdocs site from source"""

import io
import os
import logging
import subprocess
from typing import Tuple

from gwmh.job import common


def _build_mkdocs(
    tmpdir: str, repo_name: str, branch: str, stdoutfile: io.TextIOWrapper
) -> Tuple[bool, str]:
    logging.info("Building mkdocs site")
    site_directory = os.path.join(tmpdir, "site")
    result = subprocess.run(
        ["mkdocs", "build", "-d", site_directory],
        cwd=os.path.join(tmpdir, repo_name),
        stdout=stdoutfile,
        stderr=subprocess.STDOUT,
    )
    if not result.returncode == 0:
        logging.error("Failed to build mkdocs site. Aborting.")
        return False
    return True, site_directory


def mkdocs_job(repository: str, branch: str, output_path: str):
    common._run_job(
        repository, branch, output_path, job_name="mkdocs", build_fn=_build_mkdocs
    )
