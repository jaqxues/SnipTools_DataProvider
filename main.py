#!/usr/bin/env python

from shutil import copyfile
from argparse import ArgumentParser
import sqlite3 as sl
from zipfile import ZipFile
from collections import namedtuple
from scripts.db_wrapper import DbWrapper
from scripts.serialize import gen_history, gen_server_packs, gen_server_apks, gen_latest_pack, gen_known_bugs
from os import path
import json

ExtractedPackData = namedtuple('ExtractedPackData', ('flavor', 'development', 'pack_version', 'pack_version_code',
                                                     'min_apk_version_code', 'pack_impl_class', 'sc_version'))


def new_pack_extract(pack_name: str):
    assert path.isfile(pack_name), f'Specified file ("{pack_name}") does not exist'
    assert pack_name.endswith('.jar'), f'Specified file ("{pack_name}" is an invalid name for a pack)'
    with ZipFile(pack_name) as zf:
        assert 'classes.dex' in zf.NameToInfo, 'classes.dex was not found in Pack, invalid pack'
        assert (manifest_name := 'META-INF/MANIFEST.MF') in zf.NameToInfo, \
            'MANIFEST.MF was not found in jar file, invalid pack'
        with zf.open(manifest_name) as mnf:
            raw_contents = (str(c.strip(), 'utf-8').split(':', 2) for c in mnf.readlines())

    contents = {c[0]: c[1] for c in raw_contents if len(c) == 2}
    attributes = 'Flavor', 'Development', 'PackVersion', 'PackVersionCode', \
                 'MinApkVersionCode', 'PackImplClass', 'ScVersion'
    for attr in contents:
        assert attr in contents, f'Missing attribute in manifest: "{attr}"'

    data = tuple(contents[attributes[i]] for i in range(len(attributes)))

    print('Supplied the following (relevant) key-value pairs in the manifest attributes')
    print()
    for name, val in zip(attributes, data):
        print(name, '-', val)
    pack_data = ExtractedPackData(*data)

    print()
    print('Input Changelog / Release Notes (leave empty to continue)')
    release_notes = []
    while i := input('Next: '):
        release_notes.append(i)
    print('Release Notes:', release_notes)
    return pack_data, release_notes


def new_pack_known_bugs(dbw: DbWrapper):
    while (i := input('Should the pack inherit Known Bugs? (y/n): ')) not in ('y', 'n'):
        pass
    if i == 'n':
        return
    print()

    print('Choose what Known Bugs the Pack should inherit (by ScVersion and Pack)')
    sc_versions = tuple(dbw.get_sc_versions())
    for i, sc_version in zip(range(20), sc_versions):
        print(f'{i:2}', '-', sc_version)
    sc_version = sc_versions[int(input('Label of Snapchat version: '))]
    print('Selected Snapchat Version:', sc_versions)

    packs = tuple(dbw.get_packs_for_sc(sc_version))
    if len(packs) == 1:
        pack = packs[0]
    else:
        print('Choose a pack that supports snapchat version')
        for idx, pack in enumerate(packs):
            print(idx, '-', pack)
        pack = packs[int(input('Label of pack: '))]
    print('Inheriting Bugs from selected Pack:', pack)
    return pack.id


def new_pack_remove_bugs(dbw: DbWrapper, current):
    to_remove = []
    kbs = tuple(dbw.get_active_known_bugs(current))
    if not kbs:
        return to_remove
    print('Choose what bugs you want to mark as fixed for the current Pack (Leave empty to continue)')
    for idx, kb in enumerate(kbs):
        print(idx, '-', kb)
    while i := input('Input next Label: '):
        try:
            to_remove.append(kbs[int(i)])
        except ValueError:
            print("Input should be an Id (integer)")
    return to_remove


def new_pack_add_bugs(dbw: DbWrapper):
    print('Input new Known Bugs')
    print('Existing Categories:', ', '.join(dbw.get_existing_descriptions()))
    new_bugs = []
    while cat := input("Input the new report's category: "):
        if not (des := input("Input the new report's description: ")):
            print('Empty description for new bug report, ignoring current entry')
            continue
        new_bugs.append((cat, des))
    return new_bugs


def add_new_pack(dbw: DbWrapper, pack_name):
    data, release_notes = new_pack_extract(pack_name)

    print()
    print('Copy file to', copy_path := 'Packs/Files/' + path.basename(pack_name))
    copyfile(pack_name, copy_path)

    previous = new_pack_known_bugs(dbw)
    print()
    print('Inserting Pack into Database')
    current = dbw.insert_pack(pack_name, data.sc_version, data.pack_version, data.pack_version_code,
                              data.min_apk_version_code, '\n'.join(release_notes))
    if previous:
        print('Inheriting KnownBugs from selected pack')
        dbw.inherit_bugs_from(previous, current)
    while (i := input('Do you want to edit associated bugs? (y/n): ')) not in ('y', 'n'):
        pass
    if i == 'n':
        return
    if remove_bugs := new_pack_remove_bugs(dbw, current):
        print('Removing specified bugs:', remove_bugs)
        for kb in remove_bugs:
            if not kb.fixed_on:
                dbw.mark_bug_as_fixed(kb.id)
            print('Marking bug as fixed (setting date to now):', kb)
            dbw.fix_bug_for(kb.id, current)
    print()
    if new_bugs := new_pack_add_bugs(dbw):
        print('Adding specified bugs (category, description):', new_bugs)
        for cat, des in new_bugs:
            bug_id = dbw.insert_bug(cat, des)
            dbw.link_bug(bug_id, current)


def add_new_apk(dbw: DbWrapper, apk_dir, apk_name=None):
    with open(path.join(apk_dir, 'output-metadata.json'), 'r') as f:
        info = json.loads(f.read())
    v = info['version']
    if v != 3:
        raise Exception(f'output-metadata.json has an unsupported output format version (v{v}). Aborting Operation')
    el = info['elements']
    if (l := len(el)) != 1:
        raise Exception(f'Cannot handle an element array of length {l} != 1. Aborting Operation')
    el = el[0]
    version_code, version_name, file_name = el['versionCode'], el['versionName'], el['outputFile']
    apk_name = apk_name or file_name

    release_notes = []
    print('Input Changelogs (Leave empty to continue)')
    while i := input('Input next Release note: '):
        release_notes.append(i)

    dbw.insert_apk(apk_name, version_code, version_name, '\n'.join(release_notes))
    copyfile(path.join(apk_dir, file_name), path.join('Apks', 'Files', apk_name))


def gen_files(dbw):
    gen_server_packs(dbw.get_latest_packs())

    for pack in dbw.get_latest_packs():
        gen_latest_pack(pack)

    for sc_version in dbw.get_sc_versions():
        packs = tuple(dbw.get_packs_for_sc(sc_version))
        gen_history(sc_version, packs)

        known_bugs = {pack.pack_version: tuple(dbw.get_active_known_bugs(pack.id)) for pack in packs}
        gen_known_bugs(sc_version, known_bugs)

    gen_server_apks(dbw.get_latest_apk())


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-t', '--test', action='store_true',
                        help='Running in test mode (on a database called "test.db")')
    parser.add_argument('-db', '--db-name',
                        help='Specify a database name (default: releases.db)')
    parser.add_argument('-np', '--new-pack',
                        help='Specifies that a new Pack should be released (Path to Pack as argument)')
    parser.add_argument('-ng', '--no-gen-files', action='store_true',
                        help='If specified, the files are not regenerated')
    parser.add_argument('-na', '--new-apk',
                        help='Insert (and release) a new APK to the repo. (Path to APK output dir as argument')
    parser.add_argument('-an', '--apk-name',
                        help='Specifies name of the APK to be used')
    args = parser.parse_args()

    db_name = args.db_name or ('test.db' if args.test else 'releases.db')

    should_create = not path.isfile(db_name)
    with sl.connect(db_name, detect_types=sl.PARSE_COLNAMES) as con:
        db_wrapper = DbWrapper(con)
        if should_create:
            db_wrapper.create_db()

        if pack_name := args.new_pack:
            print('Adding new Pack to packs.db')
            add_new_pack(db_wrapper, pack_name)
        elif apk_dir := args.new_apk:
            print('Adding new APK to packs.db')
            add_new_apk(db_wrapper, apk_dir, args.apk_name)
        if not args.no_gen_files:
            print('Regenerating Files')
            gen_files(db_wrapper)
