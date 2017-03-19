#!/bin/bash -ex

BZR_WORK_TREE="/opt/src/maas/trunk-bzr"
GIT_WORK_TREE="/opt/src/maas/trunk-git"
TEMP_DIR="$(mktemp -d)"

function finish {
    rm -rf "$TEMP_DIR"
    rm -rf "$BZR_WORK_TREE"
}

trap "finish \$?" EXIT

SOURCE_BRANCH=/opt/src/maas/trunk

rm -rf "$BZR_WORK_TREE"

GIT_REPO=/opt/src/maas/git

# if [ ! -d "$GIT_REPO" ]; then
#     cd "$GIT_REPO"
#     git init --bare .
# fi

echo "Please modify this script to deal with an existing git tree."
read
read
read

# rm -rf "$GIT_WORK_TREE"
mkdir -p $GIT_WORK_TREE
cd "$GIT_WORK_TREE"
git init .


bzr branch $SOURCE_BRANCH $BZR_WORK_TREE
cd "$BZR_WORK_TREE"
revisions=$(bzr revno)

cur=1
while [ $cur -le $revisions ]; do
    cd "$BZR_WORK_TREE"
    bzr update -r $cur
    # log="$(bzr log -r $cur -n1 | tail -n +2)"
    log="$(bzr log -r $cur -n1 | grep '^message:$' -A 9999999 | tail -n +2 | sed 's/^  //g')"
    committer=$(bzr log -r $cur | grep ^committer | head -1 | cut -d: -f 2- | xargs echo)
    author=$(bzr log -r $cur | grep ^author | head -1 | cut -d: -f 2- | xargs echo)
    if [ "$author" == "" ]; then
        author="$committer"
    fi
    timestamp=$(bzr log -r $cur | grep ^timestamp | head -1 | cut -d: -f 2- | xargs echo | grep -o '[0-9]*' | head -n +5 | tr -d '\n')
    commit_date=$(bzr log -r $cur | grep ^timestamp | head -1 | cut -d: -f 2- | xargs echo)
    mv $GIT_WORK_TREE/.git $TEMP_DIR
    mv $BZR_WORK_TREE/.bzr $TEMP_DIR
    rm -rf $GIT_WORK_TREE
    mkdir $GIT_WORK_TREE
    rsync -xav $BZR_WORK_TREE/ $GIT_WORK_TREE
    cd $GIT_WORK_TREE
    find . -print0 | xargs -0 touch -t $timestamp.00
    mv $TEMP_DIR/.bzr $BZR_WORK_TREE
    mv $TEMP_DIR/.git $GIT_WORK_TREE
    cd $GIT_WORK_TREE
    git add --all
    export GIT_COMMITTER_DATE="$commit_date"
    export GIT_COMMITTER_NAME="bzr-to-git bridge"
    export GIT_COMMITTER_EMAIL="noreply@example.com"
    git commit -m "$log" --author "$author" --date "$commit_date"
    let cur=$cur+1
done
