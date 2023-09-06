import os
import tempfile
from typing import Callable
import subprocess

import datetime
import logging


def _run_job(
    repository: str,
    branch: str,
    output_path: str,
    job_name: str,
    build_fn: Callable,
) -> bool:
    logging.basicConfig(filename=os.path.join("log", f"{job_name}_job.log"),
                        format='[%(levelname)s] [%(asctime)s]: %(message)s',
                        level=logging.DEBUG)

    logging.info(f"Starting {job_name} job")

    stdoutfile = open(os.path.join("log", f"{job_name}_job_std.log"), 'w')
    stdoutfile.write(f'[{datetime.datetime.now()}]: Starting {job_name} job\n')
    stdoutfile.flush()

    repo_name = repository.split("/")[-1]

    if not os.path.isdir(output_path):
        logging.error(
            "Output path '%s' is not a directory. Aborting.", repr(output_path))
        return False

    tmpdir = tempfile.mkdtemp()
    logging.info("Created temporary working directory %s", tmpdir)

    logging.info("Cloning repository %s from GitHub, %s branch",
                 repository, branch)
    result = subprocess.run(
        ['git', 'clone', '--recursive', '-b', branch,
            'https://github.com/{}.git'.format(repository)],
        cwd=tmpdir, stdout=stdoutfile, stderr=subprocess.STDOUT)
    if not result.returncode == 0:
        logging.error(
            "Failed to clone repository %s, %s branch. Aborting.", repository, branch)
        return False

    success, site_directory = build_fn(
        tmpdir=tmpdir, repo_name=repo_name, branch=branch, stdoutfile=stdoutfile)
    if not success:
        logging.error(f"Build step '{str(build_fn)}' failed. Aborting.")
        return False

    if os.listdir(output_path):
        logging.info("Deleting contents of output directory %s", output_path)
        result = subprocess.run('rm -r {}/*'.format(output_path),
                                shell=True, stdout=stdoutfile, stderr=subprocess.STDOUT)
        if not result.returncode == 0:
            logging.error(
                "Failed to delete contents of output directory %s", output_path)
            return False

    logging.info("Copying to output directory %s", output_path)
    result = subprocess.run('cp -r * {}'.format(output_path),
                            cwd=site_directory, shell=True, stdout=stdoutfile, stderr=subprocess.STDOUT)
    if not result.returncode == 0:
        logging.error(
            "Failed to copy to output directory %s", output_path)
        return False

    logging.info("Deleting temporary working directory %s", tmpdir)
    subprocess.run(['rm', '-rf', tmpdir], stdout=stdoutfile,
                   stderr=subprocess.STDOUT)

    stdoutfile.write('[{}]: Job successful\n'.format(datetime.datetime.now()))
    stdoutfile.close()

    logging.info("Job completed succesfully!")

    return True
