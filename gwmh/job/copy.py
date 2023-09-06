"""Job to copy an already-built mkdocs site"""

import io
import os
from typing import Tuple

from gwmh.job import common

def _build_noop(
    tmpdir: str, repo_name: str, branch: str, stdoutfile: io.TextIOWrapper
) -> Tuple[bool, str]:
    return True, os.path.join(tmpdir, repo_name)


def copy_job(repository: str, branch: str, output_path: str):
    common._run_job(repository, branch, output_path, job_name="copy", build_fn=_build_noop)
