#!/usr/bin/env python3

import yaml
from pprint import pprint
from subprocess import (
    CalledProcessError,
    check_output,
)
import os
import sys
import argparse

def run(*args, **kwargs):
    try:
        return check_output(*args, **kwargs)
    except CalledProcessError:
        print("Error executing command: %r" % args)
        raise


def read_config(filename):
    with open(filename, 'r') as f:
        config = yaml.safe_load(f.read())
        return config

def rmtree(tree):
    if os.path.exists(tree):
        run(['rm', '-rf', tree])


def validate_config(config):
    if 'branches' not in config:
        print("Missing 'branches' entry in configuration.")
        raise SystemExit(2)
    if 'repo' not in config:
        print("Missing 'config.repo' entry in configuration.")
        print("This specifies the location of the git repository to push to.")
        raise SystemExit(3)
    if 'workdir' not in config:
        print("Missing 'config.workdir' entry in configuration.")
        print("This specifies the location of the work diretory.")
        print("(WARNING: contents will be deleted as needed.")
        raise SystemExit(4)
        

def setup(config):
    # Check if the destination git repository exists.
    clean = config['clean']
    workdir = os.path.abspath(config['workdir'])
    git_repo = os.path.abspath(config['repo'])
    if os.path.exists(workdir):
        rmtree(workdir)
    os.makedirs(workdir)
    tempdir = os.path.join(workdir, 'tmp')
    os.makedirs(tempdir)
    bzr_workdir = os.path.join(workdir, 'bzr')
    git_workdir = os.path.join(workdir, 'git')
    config['bzr_workdir'] = bzr_workdir
    config['git_workdir'] = git_workdir
    config['tempdir'] = tempdir
    if clean is True:
        rmtree(git_repo)
    # XXX might be nice to support remote git paths
    if not os.path.exists(git_repo):
        os.makedirs(git_repo)
        os.chdir(git_repo)
        run(['git', 'init', '--bare', '.'])
    run(['git', 'clone', git_repo, git_workdir])


def git_revno(git_branch):
    result = run(['git', 'rev-list', '--count', git_branch])
    return int(result.decode('utf-8').strip())


def bzr_branch(bzr_source, bzr_workdir):
    run(['bzr', 'branch', bzr_source, bzr_workdir])


def bzr_common_ancestor(branch_path):
    result = run(
        "bzr log -rancestor:%s --line | cut -d: -f1" % branch_path,
        shell=True)
    return int(result.decode('utf-8').strip())


def bzr_rev_to_git_rev(revno):
    result = run(
        "git log --oneline --no-merges | tail -%d | head -1 | awk '{ print $1 }'" % revno,
        shell=True)
    return result.decode('utf-8').strip()


def bzr_log(revno):
    result = run(
        "bzr log -r %d -n1 | grep '^message:$' -A 9999999 | tail -n +2 | sed 's/^  //g'" % revno,
        shell=True)
    return result.decode('utf-8').strip()


def bzr_committer(revno):
    result = run(
        "bzr log -r %d | grep ^committer | head -1 | cut -d: -f 2- | xargs echo" % revno,
        shell=True)
    return result.decode('utf-8').strip()


def bzr_author(revno):
    result = run(
        "bzr log -r %d | grep ^author | head -1 | cut -d: -f 2- | xargs echo" % revno,
        shell=True)
    return result.decode('utf-8').strip()


def bzr_timestamp(revno):
    result = run(
        "bzr log -r %d | grep ^timestamp | head -1 | cut -d: -f 2- | xargs echo | grep -o '[0-9]*' | head -n +5 | tr -d '\n'" % revno,
        shell=True)
    return result.decode('utf-8').strip()


def bzr_commit_date(revno):
    result = run(
        "bzr log -r %d | grep ^timestamp | head -1 | cut -d: -f 2- | xargs echo" % revno,
        shell=True)
    return result.decode('utf-8').strip()


def get_author_email_tuple(author, null_name, null_email):
    if '<' in author and author.endswith('>'):
        author, email = author[:-1].split('<', 1)
    else:
        email = ""
    author = author.strip()
    email = email.strip()
    if '@' in author:
        email = author
        author = author.replace('@', ' at ')
    author = author.replace('<', '')
    author = author.replace('>', '')
    if len(author) == 0:
        author = null_name
    if len(email) == 0 or '@' not in email:
        email = null_email
    return author, email


def reformat_author(author, null_name, null_email):
    author, email = get_author_email_tuple(author, null_name, null_email)
    return "%s <%s>" % (author, email)


def mirror(config, bzr_source, git_branch, trunk_branch):
    print("Mirroring: %s --> %s" % (bzr_source, git_branch))
    null_committer_name = config['null_committer_name']
    null_committer_email = config['null_committer_email']
    null_author_name = config['null_author_name']
    null_author_email = config['null_author_email']
    bzr_workdir = config['bzr_workdir']
    git_workdir = config['git_workdir']
    tempdir = config['tempdir']
    bzr_workdir_bzr = os.path.join(bzr_workdir, '.bzr')
    git_workdir_git = os.path.join(git_workdir, '.git')
    if trunk_branch is not None:
        os.chdir(bzr_workdir)
        try:
            start_revno = bzr_common_ancestor(trunk_branch[0])
        except ValueError:
            print("Unable to find common ancestor.")
            # Didn't branch from the branch we thought. Just skip it.
            return
        print("Common ancestor: %d" % start_revno)
    os.chdir(git_workdir)
    # Delete an branches that existed in the work directory.
    # We'll recreate whatever branch we need.
    rmtree(os.path.join(git_workdir, ".git", "refs", "heads"))
    try:
        run(["git", "rev-parse", "--verify", "origin/%s" % git_branch])
    except CalledProcessError:
        if trunk_branch is not None:
            run(["git", "checkout", "-fb", "__trunk__", "origin/" + trunk_branch[1]])
            start_git_rev = bzr_rev_to_git_rev(start_revno)
            print("Found starting git revision for %s: %s" % (git_branch, start_git_rev))
            run(["git", "checkout", "-fb", git_branch, start_git_rev])
            run(["git", "push", "origin", "%s:%s" % (git_branch, git_branch)])
            rmtree(os.path.join(git_workdir, ".git", "refs", "heads"))
    run(["git", "checkout", "-fb", git_branch, "origin/" + git_branch])
    git_revisions = git_revno(git_branch)
    print("Revisions already in git: %d" % git_revisions)
    os.chdir(bzr_workdir)
    revisions = int(run(['bzr', 'revno']).strip())
    for i in range(git_revisions, revisions):
        os.chdir(bzr_workdir)
        revno = i + 1
        run(['bzr', 'update', '-r', str(revno)])
        log = bzr_log(revno)
        author = bzr_author(revno)
        committer = bzr_committer(revno)
        timestamp = bzr_timestamp(revno)
        commit_date = bzr_commit_date(revno)
        pprint(log)
        if(len(author) == 0):
            author = committer
        author = reformat_author(
            author, null_author_name, null_author_email)
        committer = reformat_author(
            committer, null_committer_name, null_committer_email)
        pprint(author)
        pprint(committer)
        pprint(timestamp)
        pprint(commit_date)
        run(['mv', git_workdir_git, tempdir])
        run(['mv', bzr_workdir_bzr, tempdir])
        # Don't worry, we recover the contents from the .git directory later.
        rmtree(git_workdir)
        os.makedirs(git_workdir)
        run(['rsync', '-xav', bzr_workdir + '/', git_workdir])
        os.chdir(git_workdir)
        run('find . -print0 | xargs -0 touch -t %s.00' % timestamp, shell=True)
        run(['mv', os.path.join(tempdir, '.git'), git_workdir_git])
        run(['mv', os.path.join(tempdir, '.bzr'), bzr_workdir_bzr])
        run(['git', 'add', '--all'])
        committer_name, committer_email = get_author_email_tuple(
            committer, null_committer_name, null_committer_email)
        env = {
            'GIT_COMMITTER_DATE': commit_date,
            'GIT_COMMITTER_NAME': committer_name,
            'GIT_COMMITTER_EMAIL': committer_email,
        }
        run(['git', 'commit', '--allow-empty', '--allow-empty-message', '-m', log, '--author', author, '--date', commit_date], env=env)
        run(['git', 'push', 'origin', 'HEAD:%s' % git_branch])


def mirror_all(config):
    workdir = config['workdir']
    bzr_workdir = config['bzr_workdir']
    # The first bzr branch is considered to be "trunk".
    trunk_branch = None
    for spec in config['branches']:
        rmtree(bzr_workdir)
        bzr_source = spec['source']
        git_branch = spec['branch']
        bzr_branch(bzr_source, bzr_workdir)
        mirror(config, bzr_source, git_branch, trunk_branch)
        if trunk_branch is None:
            trunk_branch = (bzr_source, git_branch)

def main():
    parser = argparse.ArgumentParser(
        prog='bzr2git',
        description='Mirror bzr repositories to a git equivalent.')
    parser.add_argument(
        'config', help="Configuration file.")
    parser.add_argument(
        '-v', '--verbose', action='store_true', help="Verbose output.")
    parser.add_argument(
        '--clean', action='store_true', help="Start with a clean git repository.")
    args = parser.parse_args()
    if args.config is None:
        parser.print_help()
        raise SystemExit(1)
    config = read_config(args.config)
    if args.verbose is True:
        # XXX will be printed later
        # pprint(config)
        config['verbose'] = True
    else:
        config['verbose'] = False
    if args.clean is True and 'clean' not in config:
        config['clean'] = True
    else:
        config['clean'] = config.get('clean', False)
    validate_config(config)
    setup(config)
    if args.verbose is True:
        pprint(config)
    mirror_all(config)


if __name__ == '__main__':
    sys.exit(main())
