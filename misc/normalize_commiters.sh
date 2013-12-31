#!/bin/sh
 
git filter-branch -f --env-filter '

nn="Stefan Wolf"
oe="boeserwolf91@googlemail.com"
ne="$oe"

an="$GIT_AUTHOR_NAME"
am="$GIT_AUTHOR_EMAIL"
cn="$GIT_COMMITTER_NAME"
cm="$GIT_COMMITTER_EMAIL"
 
if [ "$GIT_COMMITTER_EMAIL" = "$oe" ]
then
cn="$nn"
cm="$ne"
fi
if [ "$GIT_AUTHOR_EMAIL" = "$oe" ]
then
an="$nn"
am="$ne"
fi
 
export GIT_AUTHOR_NAME="$an"
export GIT_AUTHOR_EMAIL="$am"
export GIT_COMMITTER_NAME="$cn"
export GIT_COMMITTER_EMAIL="$cm"
'
