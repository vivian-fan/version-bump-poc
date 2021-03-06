import os
import sys
import time
import shutil
import yaml
import git
import json
from json.decoder import JSONDecodeError
import operator
from stat import ST_CTIME


def get_remote():
    username = "vivian-fan"
    password = sys.argv[3]
    remote = f"https://{username}:{password}@github.com/vivian-fan/version-bump-poc.git"
    return remote


def get_clone_repo(remote, path, branch):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)
    clone_repo = git.Repo.clone_from(remote, path, branch=branch)
    return clone_repo


def read_intents(path, intent_file):
    with open(path + "/" + intent_file, "r") as intent_content:
        return yaml.safe_load(intent_content)


def get_version(path, file):
    with open(path + "/" + file, "r") as spec_content:
        spec_content = yaml.safe_load(spec_content)
    return spec_content["info"]["version"]


def minor_bump(version):
    major, minor, patch = version.split(".")
    return major + "." + str(int(minor) + 1) + "." + patch


def major_bump(version):
    major, minor, patch = version.split(".")
    return str(int(major) + 1) + "." + "0" + "." + patch


def is_less_than(version1, version2):
    version1 = version1.replace(".", "")
    version2 = version2.replace(".", "")
    return version1 < version2


def compute_next_version(intent, latest_release_version, target_branch_version):
    next_version = None
    if intent == "minor":
        next_version = minor_bump(latest_release_version)
    else:
        next_version = major_bump(latest_release_version)
    if is_less_than(next_version, target_branch_version):
        next_version = target_branch_version
    return next_version

def mostRecentIntentFile(path):
    all_files = os.listdir(path);
    file_times = dict();
    for file in all_files:
        if file.endswith("intent.yml"):
            file_times[file] = time.time() - os.stat(path + "/" + file).st_ctime;
    return  sorted(file_times.items(), key=operator.itemgetter(1))[0][0]

feature_branch = str(sys.argv[1])
target_branch = str(sys.argv[2])

release_path = "./release"
target_path = "./" + target_branch
feature_path = "./" + feature_branch

remote = get_remote()

clone_repo_target = get_clone_repo(remote, target_path, target_branch)
clone_repo_feature = get_clone_repo(remote, feature_path, feature_branch)

release_branches = []
for branch in clone_repo_target.refs:
    if branch.__str__().startswith("origin/production_release"):
        release_branches.append(branch.__str__())
release_branches.sort()
latest_release_branch = release_branches[-1].replace("origin/", "")

clone_repo_release = get_clone_repo(remote, release_path, latest_release_branch)

next_version_list = {"include": []}

recent_intent_file = mostRecentIntentFile(feature_path + "/")
# for commit in clone_repo_feature.iter_commits(feature_branch):
#     for file in commit.stats.files:
#         if file.endswith("intent.yml"):
#             newly_committed_intent_file = file
#             print('debug: ', commit, file)

intents = read_intents(feature_path, recent_intent_file)

for file_name, intent in intents["intent"].items():
    file = file_name + ".yaml"
    latest_release_version = get_version(release_path, file)
    target_branch_version = get_version(target_path, file)
    next_version = compute_next_version(
        intent, latest_release_version, target_branch_version
    )
    next_version_list["include"].append({"file": file, "version": next_version})

shutil.rmtree(release_path)
shutil.rmtree(target_path)
shutil.rmtree(feature_path)

print(json.dumps(next_version_list))
