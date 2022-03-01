import os
import sys
import shutil
import yaml
import git
import json


def get_remote():
    username = "vivian-fan"
    password = sys.argv[1]
    remote = f"https://{username}:{password}@github.com/vivian-fan/version_bump_poc.git"
    return remote


def get_clone_repo(remote, path, branch):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)
    clone_repo = git.Repo.clone_from(remote, path, branch=branch)
    return clone_repo


def get_intents(path, file):
    with open(path + "/" + file, "r") as stream:
        return yaml.safe_load(stream)


def get_intent_files(path):
    intent_files = [
        f
        for f in listdir(path + "/")
        if isfile(join(path + "/", f)) and f.name.endswith("intent.yml")
    ]
    return intent_files

def push_to_origin(target_path, target_branch):
    try:
        repo = git.Repo(target_path)
        repo.git.add(update=True)
        repo.index.commit("delete released intent files")
        repo.git.push("origin", target_branch)
    except Exception as e:
        print("Errors occured while pushing the code", e)
        

def delete_released_intent_files(path, released_intent_files, branch):
    for f in listdir(path + "/"):
        if isfile(join(path + "/", f)) and f.name.endswith("intent.yml"):
            if f.name in released_intent_files:
                os.remove(f)
    push_to_origin(path, branch) 


def get_version(path, file):
    file += ".yaml"
    with open(path + "/" + file, "r") as spec_file:
        spec_content = yaml.safe_load(spec_file)
    return spec_content["info"]["version"]


def combine_intents(path, unreleased_intent_files):
    intent_dic = {}
    for file in unreleased_intent_files:
        intents = get_intents(path, file)
        for fileName, intent in intents["intent"].items():
            if fileName not in intent_dic:
                intent_dic[fileName] = intent
            else:
                if intent == "major":
                    intent_dic[fileName] = intent
    return intent_dic


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


def compute_version(intent, latest_release_version, target_branch_version):
    next_version = None
    if intent == "minor":
        next_version = minor_bump(latest_release_version)
    else:
        next_version = major_bump(latest_release_version)
    if is_less_than(next_version, target_branch_version):
        next_version = target_branch_version
    return next_version


def recalculate_version(version_matrix, intent_dic, target_branch):
    for file in intent_dic:
        file_name = file + ".yaml"
        latest_release_version = get_version("./release", file)
        target_branch_version = get_version("./" + target_branch, file)
        new_version = compute_version(
            intent_dic[file], latest_release_version, target_branch_version
        )
        version_matrix["include"].append(
            {"file": file_name, "version": new_version, "branch": target_branch}
        )


master_path = "./master"
dev_path = "./develop"
release_path = "./release"

clone_repo_master = get_clone_repo(remote, master_path, "master")
clone_repo_dev = get_clone_repo(remote, dev_path, "develop")

release_branches = []
for branch in clone_repo_master.refs:
    if branch.__str__().startswith("origin/production_release"):
        release_branches.append(branch.__str__())
release_branches.sort()
latest_release_branch = release_branches[-1].replace("origin/", "")
clone_repo_release = get_clone_repo(remote, release_path, latest_release_branch)

released_intent_files = get_intent_files(release_path)
delete_released_intent_files(master_path, released_intent_files, "master")
unreleased_intent_files_master = get_intent_files(master_path)
delete_released_intent_files(dev_path, released_intent_files, "develop")
unreleased_intent_files_dev = get_intent_files(dev_path)

version_matrix = {"include": []}


intent_dic_master = combine_intents(master_path, unreleased_intent_files_master)
recalculate_version(version_matrix, intent_dic_master, "master")

intent_dic_dev = combine_intents(dev_path, unreleased_intent_files_dev)
recalculate_version(version_matrix, intent_dic_dev, "develop")

print(json.dumps(version_matrix))
