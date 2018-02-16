# Script to create a git-annex repo compatible with git-pynex
# (git-annex has some problematic defaults, so git-pynex uses
# overriden settings right away.)
git init
git -c annex.tune.objecthashlower=true annex init "test repo"
