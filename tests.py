import os
import shutil
from subprocess import check_call, check_output


#GIT_PYNEX = "git -c annex.tune.objecthashlower=true annex "
GIT_PYNEX = "git pynex "


def run(cmd):
    check_call(cmd, shell=True)


def popen(cmd):
    return check_output(cmd, shell=True).decode()


def make_file(fname, content):
    with open(fname, "w") as f:
        f.write(content)


def read_file(fname):
    with open(fname) as f:
        return f.read()


def make_repo(path):
    if os.path.exists(path):
        run("chmod -R +w " + path)
        shutil.rmtree(path) #, ignore_errors=True)
    os.makedirs(path)
    os.chdir(path)
    run("git init")
    run(GIT_PYNEX + "init test-repo")


def test_init():
    make_repo("/tmp/annex-test1")
    uuid = popen("git config annex.uuid").strip()
    assert popen("git branch") == '  git-annex\n'
    run("git checkout git-annex")
    assert sorted(os.listdir()) == ['.git', 'difference.log', 'uuid.log']


def test_add1():
    make_repo("/tmp/annex-test2")
    make_file("file1", "file1 data\n")
    run(GIT_PYNEX + "add file1")
    assert os.path.islink("file1")
    assert read_file("file1") == "file1 data\n"
    assert os.readlink("file1") == ".git/annex/objects/5de/9ee/SHA256E-s11--5eb788ac2bded6ce7112e44d68228bfecb3e569d1d745c78e1275986bbedc3cf/SHA256E-s11--5eb788ac2bded6ce7112e44d68228bfecb3e569d1d745c78e1275986bbedc3cf"
    assert popen("git status --porcelain") == "A  file1\n"
    run("git commit -m 'file1 added'")
    assert popen("git status --porcelain") == ""
    assert len(popen("git log --oneline").split("\n")) == 2  # + empty line

    make_file("file2.txt", "file2.txt data\n")
    run(GIT_PYNEX + "add file2.txt")
    assert os.path.islink("file2.txt")
    assert read_file("file2.txt") == "file2.txt data\n"
    assert os.readlink("file2.txt")  == ".git/annex/objects/f5a/2c8/SHA256E-s15--2e57e969394ef19ad8af99d18af903de0e5fa3e09dda9818b1782a7e7e0befc0.txt/SHA256E-s15--2e57e969394ef19ad8af99d18af903de0e5fa3e09dda9818b1782a7e7e0befc0.txt"

    make_file("file3.foo.bar", "file3.foo.bar data\n")
    run(GIT_PYNEX + "add file3.foo.bar")
    assert os.path.islink("file3.foo.bar")
    assert read_file("file3.foo.bar") == "file3.foo.bar data\n"
    assert os.readlink("file3.foo.bar") == ".git/annex/objects/2c7/1a8/SHA256E-s19--4a564ca152514a6cf577dc0ba25098e4f24431ff905c10436b394aa8987849d0.foo.bar/SHA256E-s19--4a564ca152514a6cf577dc0ba25098e4f24431ff905c10436b394aa8987849d0.foo.bar"

    make_file("file4.foo.bar.123", "file4.foo.bar.123 data\n")
    run(GIT_PYNEX + "add file4.foo.bar.123")
    assert os.path.islink("file4.foo.bar.123")
    assert read_file("file4.foo.bar.123") == "file4.foo.bar.123 data\n"
    assert os.readlink("file4.foo.bar.123") == ".git/annex/objects/3f1/2f3/SHA256E-s23--3b7a5fdf8072bbeefdf733b6fe88b85343343148e0e2b856a09de3267eeec406.bar.123/SHA256E-s23--3b7a5fdf8072bbeefdf733b6fe88b85343343148e0e2b856a09de3267eeec406.bar.123"

    assert popen("git status --porcelain") == 'A  file2.txt\nA  file3.foo.bar\nA  file4.foo.bar.123\n'
    run("git commit -m 'more files added'")
    assert popen("git status --porcelain") == ""
    assert len(popen("git log --oneline").split("\n")) == 3  # + empty line


def test_add2():
    make_repo("/tmp/annex-test3")
    make_file("file1", "file1 data\n")
    run(GIT_PYNEX + "add file1")
    assert os.path.islink("file1")
    run("git commit -m 'file1 added'")
    run("git checkout git-annex")

    assert sorted(os.listdir()) == ['.git', '5de', 'difference.log', 'uuid.log']
    assert os.path.isfile("5de/9ee/SHA256E-s11--5eb788ac2bded6ce7112e44d68228bfecb3e569d1d745c78e1275986bbedc3cf.log")