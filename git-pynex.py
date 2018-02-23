#!/usr/bin/env python3
# git-pynex - Subset of git-annex functionality in Python
#
# Copyright (c) 2018 Paul Sokolovsky
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import sys
import hashlib
import os
import time
import subprocess
import uuid
import argparse


dot_git_path = None
git_annex_tmp = ".git/annex/pynex-git-annex"


def anx_timestamp():
    return "%.5f0000s" % time.time()


def hash_file(fname):
    hasher = hashlib.sha256()
    with open(fname, "rb") as f:
        while 1:
            buf = f.read(16384)
            if not buf:
                break
            hasher.update(buf)
    return hasher.hexdigest()


def ensure_dir(path):
    dirpath = path.rsplit("/", 1)[0]
    if not os.path.isdir(dirpath):
        os.makedirs(dirpath)


def anx_key(fname):
    hsh = hash_file(fname)
    size = os.stat(fname)[6]
    ext = ".".join(fname.rsplit(".", 2)[1:])
    key = "SHA256E-s%d--%s" % (size, hsh)
    if ext:
        key += "." + ext
    return key


def anx_key_hash(key):
    hasher = hashlib.md5(key.encode())
    return hasher.hexdigest()


def anx_key_subpath(key):
    keyhash = anx_key_hash(key)
    return keyhash[0:3] + "/" + keyhash[3:6] + "/" + key


def anx_key_content_path(key):
    return dot_git_path + ".git/annex/objects/" + anx_key_subpath(key) + "/" + key


def anx_key_metadata_path(key):
    return dot_git_path + ".git/annex/pynex-git-annex/" + anx_key_subpath(key)


def find_dot_git():
    path = os.getcwd()
    res = "."
    while path:
        #print(path, res)
        if os.path.isdir(res + "/.git"):
            if res == ".":
                return ""
            return res[2:] + "/"
        res = res + "/.."
        path = path.rsplit("/", 1)[0]
    return None


def get_this_uuid():
    with os.popen("git config annex.uuid", "r") as f:
        return f.read().rstrip()


def assert_this_uuid():
    uuid = get_this_uuid()
    if not uuid:
        fatal("Not a git-annex repository (not initialized?)")


def assert_no_uncommitted():
    out = exec_get_line("git status -uno --porcelain")
    if out:
        fatal("There are uncommitted changes in the repository, commit them first")


def checkout_git_annex(fname="."):
    "Checkout file(s) from git-annex branch"
    if not os.path.isdir(git_annex_tmp):
        os.makedirs(git_annex_tmp)
    res = os.system("GIT_INDEX_FILE=../git-annex.index.out "
        "git --work-tree=%s checkout git-annex -- %s" % (git_annex_tmp, fname))
    assert res == 0


def open_git_annex_file(fname, mode="r"):
    return open("%s/%s" % (git_annex_tmp, fname), mode)


def exec_get_line(cmd):
    if isinstance(cmd, list):
        return subprocess.check_output(cmd).decode().strip()
    return subprocess.check_output(cmd, shell=True).decode().strip()


def commit_git_annex_file(fname, msg="update", parent="git-annex"):
    # fname can be "." to commit entire tree
    save_dir = os.getcwd()
    try:
        os.chdir(git_annex_tmp)
        subprocess.check_call("GIT_INDEX_FILE=../git-annex.index.out git --work-tree=. add %s" % fname, shell=True)
        tree_id = exec_get_line("GIT_INDEX_FILE=../git-annex.index.out git --work-tree=. write-tree")
        if parent:
            parent = "-p " + parent
        else:
            parent = ""
        commit_id = exec_get_line("GIT_INDEX_FILE=../git-annex.index.out git "
            "--work-tree=. commit-tree %s -m '%s' %s" % (parent, msg, tree_id))
        subprocess.check_call("GIT_INDEX_FILE=../git-annex.index.out git --work-tree=. update-ref refs/heads/git-annex %s" % commit_id, shell=True)
    finally:
        os.chdir(save_dir)


annex_remote_map = {}


def parse_git_config():
    global annex_remote_map
    with open(dot_git_path + ".git/config") as f:
        sec = None
        for l in f:
            l = l.rstrip()
            if l[0] == "[":
                l = l[1:-1]
                l = l.split(" ", 1)
                sec_name = None
                sec = l[0]
                if len(l) > 1:
                    sec_name = l[1].strip('"')
                #print(sec, sec_name)
            else:
                key, val = [x.strip() for x in l.split("=")]
                if key == "annex-uuid":
                    annex_remote_map[val] = sec_name


def cmd_calckey(args):
    print(anx_key(args.file))


def cmd_contentlocation(args):
    print(anx_key_content_path(args.key))


def cmd_calclocation(args):
    key = anx_key(args.file)
    print(anx_key_content_path(key))


def cmd_uuid(args):
    print(get_this_uuid())


def cmd_repos(args):
    parse_git_config()
    #print(annex_remote_map)
    here = get_this_uuid()
    checkout_git_annex("uuid.log")
    print("UUID | Created | Description | Git remote info")
    with open_git_annex_file("uuid.log") as f:
        for l in f:
            l = l.rstrip()
            uuid, l = l.split(" ", 1)
            desc, tstamp = l.rsplit(" ", 1)
            tstamp = tstamp.split("=", 1)[1][:-1]
            tstamp = float(tstamp)
            tstamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tstamp))
            if uuid == here:
                desc += " [here]"
            elif uuid in annex_remote_map:
                desc += " [git remote: %s]" % annex_remote_map[uuid]
            print("%s %s %s" % (uuid, tstamp, desc))


def parse_loc_file(fname):
    loc_map = {}
    with open(fname) as f:
        for l in f:
            tstamp, pres, uuid = l.rstrip().split(" ")
            if uuid in loc_map:
                prev_tstamp, prev_pres = loc_map[uuid]
                if tstamp < prev_tstamp:
                    continue
            loc_map[uuid] = (tstamp, int(pres))
    return loc_map


def cmd_add(args):
    assert_this_uuid()
    here = get_this_uuid()
    key = anx_key(args.file)
    path = anx_key_content_path(key)
    ensure_dir(path)
    os.rename(args.file, path)
    os.symlink(path, args.file)

    locfile = anx_key_metadata_path(key) + ".log"
    ensure_dir(locfile)

    present = False
    if os.path.exists(locfile):
        loc_map = parse_loc_file(locfile)
        #print(loc_map)
        tstamp, present = loc_map.get(here, (0, 0))

    if not present:
        with open(locfile, "a") as f:
            f.write("%s 1 %s\n" % (anx_timestamp(), here))
        commit_git_annex_file(anx_key_subpath(key) + ".log")

    subprocess.check_call(["git", "add", args.file])


def cmd_sync(args):
    assert_no_uncommitted()
    subprocess.check_call(["git", "fetch", args.remote])

    save_dir = os.getcwd()
    if dot_git_path:
        os.chdir(dot_git_path)

    subprocess.check_call(["git", "checkout", "git-annex"])
    assert not os.path.exists(".gitattributes")
    with open(".gitattributes", "w") as f:
        f.write("** merge=union\n")
    subprocess.check_call([
        "git", "merge", "--allow-unrelated-histories",
        "-m", "merging %s/git-annex into git-annex" % args.remote,
        "remotes/%s/git-annex" % args.remote
    ])
    os.remove(".gitattributes")

    # TODO: use current branch, not master
    subprocess.check_call(["git", "checkout", "master"])
    rc = subprocess.call([
        "git", "merge", "--allow-unrelated-histories",
        "--no-edit",
        #"-m", "Merge remote-tracking branch 'remotes/%s/master'" % args.remote,
        #"--log",
        "remotes/%s/master" % args.remote
    ])

    if rc == 1:
        # Assuming merge conflict
        cmd_resolvemerge(args)

    subprocess.check_call(["git", "push", args.remote, "git-annex", "master:synced/master"])

    os.chdir(save_dir)


def cmd_resolvemerge(args):
    out = exec_get_line("git status -uno --porcelain")
    commit_msg = "git-annex automatic merge conflict fix\n"
    changed = False

    for l in out.split("\n"):
        status, fname = l.split(" ", 1)
        if not os.path.islink(fname):
            continue
        linked = os.readlink(fname)
        if ".git/annex/objects/" not in linked:
            continue

        if not changed:
            print("\nAutomatically resolving annex files merge conflicts")

        #print("%s is conflicted annex file" % fname)
        if status == "AA":
            linked1 = exec_get_line(["git", "show", ":2:" + fname])
            #print(linked1)
            linked2 = exec_get_line(["git", "show", ":3:" + fname])
            #print(linked2)
            names = [fname]
            for linked in (linked1, linked2):
                key = linked.rsplit("/", 1)[1]
                key_hash = anx_key_hash(key)
                #print(key, key_hash)
                new_fname = "%s.variant-%s" % (fname, key_hash[:4])
                os.symlink(linked, new_fname)
                subprocess.check_call(["git", "add", new_fname])
                names.append(new_fname)

            subprocess.check_call(["git", "rm", "-q", fname])
            msg = "add/add conflict for '%s': resolved to '%s' (ours) and '%s' (theirs)" % tuple(names)
            print(msg)
            commit_msg += "\n" + msg
            changed = True

        else:
            assert False, status

    if changed:
        subprocess.check_call(["git", "commit", "-m", commit_msg])
        print("\n*** Merge conflict was automatically resolved; you may want to examine the result. ***\n")


def cmd_init(args):
    if os.path.isdir(git_annex_tmp):
        fatal("Annex is already initialized.")
    os.makedirs(git_annex_tmp)

    if not args.description:
        args.description = "my repo"
    my_uuid = str(uuid.uuid1())
    tstamp = anx_timestamp()

    with open_git_annex_file("uuid.log", mode="w") as f:
        f.write("%s %s timestamp=%s\n" % (my_uuid, args.description, tstamp))
    with open_git_annex_file("difference.log", mode="w") as f:
        f.write("%s fromList [ObjectHashLower] timestamp=%s\n" % (my_uuid, anx_timestamp()))

    commit_git_annex_file(".", msg="branch created", parent=None)

    subprocess.check_call(["git", "config", "annex.uuid", my_uuid])
    subprocess.check_call(["git", "config", "annex.version", "5"])
    subprocess.check_call(["git", "config", "annex.tune.objecthashlower", "true"])


def cmd_git_annex_co(args):
    checkout_git_annex()


def cmd_git_annex_cat(args):
    checkout_git_annex()
    with open_git_annex_file(args.file) as f:
        print(f.read())


def cmd_help(args):
    argp.print_help()
    sys.exit(0)


def fatal(msg):
    sys.stderr.write("git-pynex: %s\n" % msg)
    sys.exit(1)


argp = argparse.ArgumentParser(description="Subset of git-annex reimplemented in Python")
argp.set_defaults(func=None)

subparsers = argp.add_subparsers(title="Commands", metavar="")

subargp = subparsers.add_parser("init", help="initialize annex repository")
subargp.add_argument("description", nargs="?", help="human-readable repository description")
subargp.set_defaults(func=cmd_init)

subargp = subparsers.add_parser("add", help="schedule addition of a file to repository")
subargp.add_argument("file")
subargp.set_defaults(func=cmd_add)

subargp = subparsers.add_parser("sync", help="sync repo metadata with a specific remote")
subargp.add_argument("remote")
subargp.set_defaults(func=cmd_sync)

subargp = subparsers.add_parser("resolvemerge", help="resolve merge conflicts in annexed files")
subargp.set_defaults(func=cmd_resolvemerge)

subargp = subparsers.add_parser("uuid", help="print UUID of current repository")
subargp.set_defaults(func=cmd_uuid)

subargp = subparsers.add_parser("repos", help="show repositories")
subargp.set_defaults(func=cmd_repos)

subargp = subparsers.add_parser("calckey", help="calculates the key that would be used to refer to a file")
subargp.add_argument("file")
subargp.set_defaults(func=cmd_calckey)

subargp = subparsers.add_parser("contentlocation", help="looks up content for a key")
subargp.add_argument("key")
subargp.set_defaults(func=cmd_contentlocation)

subargp = subparsers.add_parser("calclocation", help="calculates the annex location that would be used to refer to a file")
subargp.add_argument("file")
subargp.set_defaults(func=cmd_calclocation)

subargp = subparsers.add_parser("git-annex-co", help="checkout git-annex branch")
subargp.set_defaults(func=cmd_git_annex_co)

subargp = subparsers.add_parser("git-annex-cat", help="cat file from git-annex branch")
subargp.add_argument("file")
subargp.set_defaults(func=cmd_git_annex_cat)

args = argp.parse_args()
#print(args)

if args.func is None:
    cmd_help(args)

dot_git_path = find_dot_git()
if dot_git_path is None:
    fatal("Not in a git repository.")

git_annex_tmp = dot_git_path + git_annex_tmp

args.func(args)
