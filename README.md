git-pynex
=========

git-pynex is a proof-of-concept reimplementation of a subset of git-annex
functionality in Python.

What is git-annex and why it needs to be cloned, especially if incomplete?
-------------------------------------------------------------------------

[git-annex](https://git-annex.branchable.com) is (large) file archive
management system implemented on top of git. It's faily advanced and
well-thought one, and in development for quite some time. It's also
written in Haskel. This fact is pretty cool too, but maybe - just
maybe - your friends don't know it. Worse, maybe you don't know it.
Then maybe you would have a reservation about using a program
written in a cool obscure and esotoric language for managing your
personal data archive. After all, an archive is about reliability and
accessibility, and obscurity and esotericity don't mix too well with
that. If something goes wrong, will you be able to fix it? Will your
friends be able to help you? Will you be able to access your archive
on some system X, or deploy it on your future file server of unknown
architecture with just basic toolchain from a vendor (no Haskel
compiler?). If these points ring a bell, where an idea to reimplement
function of git-annex in a more popular language comes from.

git-annex has also other arguable "drawbacks". For example, it clearly
doesn't follow Unix' "do one thing and do it right". It can do a lot
of things, which is of course always cool. It always leaves an impression
that the system is complex and maybe (maybe not) scares users. It's
also harder to support it - there are known cases when system integrator
whhich initially adopted git-annex dropped support of it in favor of
git-lfs. git-pynex doesn't try to reimplement git-annex in all of its
glory, just a subset of it.

How git-annex/pynex compare to git-lfs?
----------------------------------------

They serves completely different purposes and usecases. The ideas behind
git-lfs are simple: a) people want to store large files in git; b) but
doing that is inefficient. So, git-lfs adds large file support which blends
as much as possible into standard git workflow. For example, when a user
clone git-lfs repository, they expect to get it complete (with all large
files).

git-annex (and thus git-pynex), on the other hand, is digital archive
management system built on *top* of git. The usecase it serves is:

1. You have an archive of 100,000s of files, with a volume of several
   terabytes. Most of your systems can't store such a volume of data
   at once, so you want "placeholders" (and some metadata) of the files
   by default, but be able to request any subset of the files easily.
   Then "unrequest" that subset and request another.

Beyond that initial usecase, there's a following one:

2. Maybe you don't a centralized archive of 100,000s of files, and
   several TBs in the first place. Maybe your achive is distributed,
   so 50,000 of files are kept in one place, and another 50,000 in
   another place. Each file may be kept in more than one place, thus
   allowing redundancy and data backup capabilities.

If you need such functionality, git-annex is for you, and git-pynex
is an alternative implementation, a "2nd choice", of it, designed to
alleviate some concerns with git-annex implementation. If you just
need to keep large files in a git repository, git-lfs (or its
alternatives) is a better match for you.

Status
------

git-pynex is currently in the "proof of concept" implementation stage.
The idea is to treat git-annex operation is a black box, and try to
reimplement it in Python3, initially as a drop-in replacement by
sub-functionality of some commands.

Right from the start, it's accepted that some historical choices of
git-annex where not ideal, and git-pynex starts with non-default, but
more scalable, choices for some options. For example, git-annex by
default relies on case-sensitive filesystem to maintain its structure,
while an option exists to not rely on the case-sensitivity. We use
this option, `annex.tune.objecthashlower=true`, from the start.
