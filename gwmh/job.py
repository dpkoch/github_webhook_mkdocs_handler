import os
import tempfile
import subprocess

import datetime
import logging


def mkdocs_job(repository, branch, output_path):
    logging.basicConfig(filename='log/mkdocs_job.log',
                        format='[%(levelname)s] [%(asctime)s]: %(message)s',
                        level=logging.DEBUG)

    logging.info("Starting MkDocs build job")

    stdoutfile = open('log/mkdocs_job_std.log', 'w')
    stdoutfile.write('[{}]: Starting MkDocs build job\n'.format(
        datetime.datetime.now()))
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

    logging.info("Building mkdocs site")
    result = subprocess.run(
        ['mkdocs', 'build', '-d', '../site'], cwd='{}/{}'.format(tmpdir, repo_name), stdout=stdoutfile, stderr=subprocess.STDOUT)
    if not result.returncode == 0:
        logging.error("Failed to build mkdocs site. Aborting.")
        return False

    if os.listdir(output_path):
        logging.info("Deleting contents of output directory %s", output_path)
        result = subprocess.run('rm -r {}/*'.format(output_path),
                                shell=True, stdout=stdoutfile, stderr=subprocess.STDOUT)
        if not result.returncode == 0:
            logging.error(
                "Failed to delete contents of output directory %s", output_path)
            return False

    logging.info("Copying mkdocs site to output directory %s", output_path)
    result = subprocess.run('cp -r * {}'.format(output_path),
                            cwd='{}/site'.format(tmpdir), shell=True, stdout=stdoutfile, stderr=subprocess.STDOUT)
    if not result.returncode == 0:
        logging.error(
            "Failed to copy mkdocs site to output directory %s", output_path)
        return False

    logging.info("Deleting temporary working directory %s", tmpdir)
    subprocess.run(['rm', '-rf', tmpdir], stdout=stdoutfile,
                   stderr=subprocess.STDOUT)

    stdoutfile.write('[{}]: Job successful\n'.format(datetime.datetime.now()))
    stdoutfile.close()

    logging.info("Mkdocs build job completed succesfully!")

    return True
