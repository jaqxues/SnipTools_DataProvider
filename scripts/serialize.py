import json
from pathlib import Path
from os import path


def _get_pack_info_dir(dir, file_name):
    t = path.join('Packs/Info/', dir)
    Path(t).mkdir(parents=True, exist_ok=True)
    return path.join(t, file_name)


def gen_latest_pack(pack):
    values = {
        'pack_version': pack.pack_version,
        'pack_v_code': pack.pack_v_code
    }
    with open(_get_pack_info_dir('Updates', f'Latest_Sc_v{pack.sc_version}.json'), 'w+') as f:
        json.dump(values, f)


def gen_history(sc_version, packs):
    values = [{
        'pack_version': pack.pack_version,
        'pack_v_code': pack.pack_v_code
    } for pack in packs]
    with open(_get_pack_info_dir('History', f'History_Sc_v{sc_version}.json'), 'w+') as f:
        json.dump(values, f)


def gen_known_bugs(sc_version, known_bugs):
    known_bugs = {pack_version: tuple(
        {
            'filed_on': _serialize_date(bug.filed_on),
            'description': bug.description,
            'category': bug.category,
            'fixed_on': _serialize_date(bug.fixed_on)
        } for bug in bugs) for (pack_version, bugs) in known_bugs.items()}
    with open(_get_pack_info_dir('KnownBugs', f'KnownBugs_Sc_v{sc_version}.json'), 'w+') as f:
        json.dump(known_bugs, f)


def gen_server_packs(packs):
    values = tuple(
        {
            'sc_version': pack.sc_version,
            'name': pack.name,
            'pack_version': pack.pack_version,
            'pack_v_code': pack.pack_v_code,
            'min_apk_v_code': pack.min_apk_v_code
        }
        for pack in packs)
    with open(_get_pack_info_dir('', 'ServerPacks.json'), 'w+') as f:
        json.dump(values, f)


def _serialize_date(date):
    if date:
        return int(date.timestamp() * 1000)
    return -1
