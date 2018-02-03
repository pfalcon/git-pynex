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
import argparse


dot_git_path = None
git_annex_tmp = ".git/annex/pynex-git-annex"


def hash_file(fname):
    hasher = hashlib.sha256()
    with open(fname, "rb") as f:
        while 1:
            buf = f.read(16384)
            if not buf:
                break
            hasher.update(buf)
    return hasher.hexdigest()


def anx_key(fname):
    hsh = hash_file(fname)
    size = os.stat(fname)[6]
    ext = ".".join(fname.rsplit(".", 2)[1:])
    return "SHA256E-s%d--%s.%s" % (size, hsh, ext)


def anx_key_hash(key):
    hasher = hashlib.md5(key.encode())
    return hasher.hexdigest()


def anx_key_path(key):
    keyhash = anx_key_hash(key)
    return dot_git_path + "/.git/annex/objects/" + keyhash[0:3] + "/" + keyhash[3:6] + "/" + key


def find_dot_git():
    path = os.getcwd()
    res = "."
    while path:
        #print(path, res)
        if os.path.isdir(res + "/.git"):
            return res
        res = res + "/.."
        path = path.rsplit("/", 1)[0]
    return None


def get_this_uuid():
    with os.popen("git config annex.uuid", "r") as f:
        return f.read().rstrip()


def checkout_git_annex(fname="."):
    "Checkout file(s) from git-annex branch"
    if not os.path.isdir(git_annex_tmp):
        os.makedirs(git_annex_tmp)
    res = os.system("GIT_INDEX_FILE=../git-annex.index.out "
        "git --work-tree=%s checkout git-annex -- %s" % (git_annex_tmp, fname))
    assert res == 0


def open_git_annex_file(fname):
    return open("%s/%s" % (git_annex_tmp, fname))


annex_remote_map = {}


def parse_git_config():
    global annex_remote_map
    with open(dot_git_path + "/.git/config") as f:
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
    print(anx_key_path(args.key))


def cmd_calclocation(args):
    key = anx_key(args.file)
    print(anx_key_path(key))


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


def cmd_git_annex_co(args):
    checkout_git_annex()


def cmd_git_annex_cat(args):
    checkout_git_annex()
    with open_git_annex_file(args.file) as f:
        print(f.read())


argp = argparse.ArgumentParser(description="Subset of git-annex reimplemented in Python")

subparsers = argp.add_subparsers(title="Commands", metavar="")

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

dot_git_path = find_dot_git()
git_annex_tmp = dot_git_path + "/" + git_annex_tmp

args.func(args)
