import sqlite3 as sl
from scripts.db_wrapper import DbWrapper
from scripts.serialize import gen_latest_pack, gen_history, gen_known_bugs, gen_server_packs
from os import path

db_name = 'packs.db'


def gen_files():
    should_create = not path.isfile(db_name)
    with sl.connect(db_name) as con:
        db_wrapper = DbWrapper(con)
        if should_create:
            db_wrapper.create_db()
            db_wrapper.add_sample_data()

        gen_server_packs(db_wrapper.get_latest_packs())

        for pack in db_wrapper.get_latest_packs():
            gen_latest_pack(pack)

        for sc_version in db_wrapper.get_sc_versions():
            packs = tuple(db_wrapper.get_packs_for_sc(sc_version))
            gen_history(sc_version, packs)

            known_bugs = {pack.pack_version: tuple(db_wrapper.get_known_bugs(pack.id)) for pack in packs}
            gen_known_bugs(sc_version, known_bugs)


if __name__ == '__main__':
    gen_files()
