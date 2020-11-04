import sqlite3 as sl
from scripts.db_wrapper import DbWrapper
from scripts.serialize import gen_latest_pack, gen_history, gen_known_bugs, gen_server_packs, gen_server_apks
from os import path

db_name = 'releases.db'


def add_sample_data(dbw: DbWrapper):
    apk_ids = [dbw.insert_apk("SnipTools_Release", 2, "1.0.1"),
               dbw.insert_apk("SnipTools_Release", 4, "1.1.0")]
    pack_ids = [dbw.insert_pack('Pack_v1', '10.48.5.0', '1.2.0', 10, 1, 'Updated for 10.48.5.0'),
                dbw.insert_pack('Pack_v2', '10.48.5.0', '1.2.1', 11, 2, 'Fixed Saving'),
                dbw.insert_pack('Pack_v3', '10.49.5.0', '1.2.3', 12, 2, 'Updated for 10.49')]

    bug_ids = [dbw.insert_bug('Saving', 'Currently does not work'),
               dbw.insert_bug('Screenshot Bypass', 'Randomly stopped working')]

    dbw.link_bug(bug_ids[0], pack_ids[0])

    dbw.inherit_bugs_from(pack_ids[0], pack_ids[1])
    dbw.link_bug(bug_ids[1], pack_ids[1])

    dbw.inherit_bugs_from(pack_ids[1], pack_ids[2])
    dbw.mark_bug_as_fixed(bug_ids[0])
    dbw.fix_bug_for(bug_ids[0], pack_ids[2])


def gen_files(test=False):
    should_create = not path.isfile(db_name)
    with sl.connect(db_name, detect_types=sl.PARSE_COLNAMES) as con:
        db_wrapper = DbWrapper(con)
        if should_create:
            db_wrapper.create_db()
            if test:
                add_sample_data(db_wrapper)

        gen_server_packs(db_wrapper.get_latest_packs())

        for pack in db_wrapper.get_latest_packs():
            gen_latest_pack(pack)

        for sc_version in db_wrapper.get_sc_versions():
            packs = tuple(db_wrapper.get_packs_for_sc(sc_version))
            gen_history(sc_version, packs)

            known_bugs = {pack.pack_version: tuple(db_wrapper.get_active_known_bugs(pack.id)) for pack in packs}
            gen_known_bugs(sc_version, known_bugs)

        gen_server_apks(db_wrapper.get_latest_apk())


if __name__ == '__main__':
    test = False
    if test:
        db_name = 'test.db'
        gen_files(True)
    else:
        gen_files()
