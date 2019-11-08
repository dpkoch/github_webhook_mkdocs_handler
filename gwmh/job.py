import os
import tempfile
import subprocess


def mkdocs_job(repository, branch, output_path):
    print("="*80)
    print("  Starting mkdocs build job")
    print("="*80)

    repo_name = repository.split("/")[-1]

    if not os.path.isdir(output_path):
        print("[ERROR] Output path {} is not a directory. Aborting.".format(output_path))
        return False

    tmpdir = tempfile.mkdtemp()
    print("[ INFO] Created temporary working directory {}".format(tmpdir))

    print("[ INFO] cloning repository {} from GitHub".format(repository))
    result = subprocess.run(
        ['git', 'clone', '--recursive', 'https://github.com/{}.git'.format(repository)], cwd=tmpdir)
    if not result.returncode == 0:
        print("[ERROR] Failed to clone repository {}. Aborting.".format(repository))
        return False

    print("[ INFO] Building mkdocs site")
    result = subprocess.run(
        ['mkdocs', 'build', '-d', '../site'], cwd='{}/{}'.format(tmpdir, repo_name))
    if not result.returncode == 0:
        print("[ERROR] Failed to build mkdocs site. Aborting.")
        return False

    print("[ INFO] Copying mkdocs site to output directory {}".format(output_path))
    result = subprocess.run('cp -r * {}'.format(output_path),
                            cwd='{}/site'.format(tmpdir), shell=True)
    if not result.returncode == 0:
        print("[ERROR] Failed to copy mkdocs site to output directory {}".format(output_path))
        return False

    print("[ INFO] Deleting temporary working directory {}".format(tmpdir))
    subprocess.run(['rm', '-rf', tmpdir])

    print("[ INFO] Mkdocs build job completed succesfully!")
    print("="*80)

    return True
