#!/usr/bin/env python3

import collections
import csv
import pathlib
import re
import ck2parser
import print_time


@print_time.print_time
def main():
    parser = ck2parser.SimpleParser(ck2parser.rootpath / 'SWMH-BETA/SWMH')
    ck2localize = ck2parser.get_localisation(parser.moddirs)
    title_key = {title: 'PROV{}'.format(prov) for prov, title, _ in ck2parser.get_provinces(parser)}
    parser.moddirs = []

    eu4root = pathlib.Path('/cygdrive/c/SteamLibrary/steamapps/common/Europa Universalis IV')
    localize = {}
    for path in (eu4root / 'localisation').glob('*_l_english.yml'):
        with path.open(encoding='utf-8-sig') as f:
            for line in f:
                match = re.fullmatch(r'\s*([^#\s:]+):\d?\s*"(.*)"[^"]*', line)
                if match:
                    localize[match.group(1)] = match.group(2)
    areas, regions, superregions = {}, {}, collections.OrderedDict()
    for n, v in parser.parse_file(eu4root / 'map/area.txt'):
        areas[n.val] = [v2.val for v2 in v]
    for n, v in parser.parse_file(eu4root / 'map/region.txt'):
        regions[n.val] = [v3.val for _, v2 in v for v3 in v2]
    for n, v in parser.parse_file(eu4root / 'map/superregion.txt'):
        superregions[n.val] = [v2.val for v2 in v]
    history = {}
    for path in (eu4root / 'history/provinces').iterdir():
        num = int(re.match(r'\d+', path.stem).group())
        history[num] = path.stem
    names = collections.defaultdict(list)
    for path in (eu4root / 'common/province_names').iterdir():
        with path.open() as f:
            for line in f:
                match = re.fullmatch(r' *(\d+) *= *"([^"]*)"\n?', line)
                if match and match.group(2) not in names[int(match.group(1))]:
                    names[int(match.group(1))].append(match.group(2))
    for n, v in localize.items():
        if re.fullmatch(r'PROV\d+', n):
            num = int(n[4:])
            if v in names[num]:
                names[num].remove(v)
            names[num].insert(0, v)

    # count = 0
    off_map = [set(), set(), set(), set()]
    prov_mappings = collections.defaultdict(list)
    try:
        with open('province_table_new.csv', encoding='cp1252') as f:
            for line in f:
                match = re.match(r'([^#;]*);([^#;]*)', line)
                if match:
                    prov_mappings[int(match.group(2))].append(match.group(1))
                else:
                    match = re.match(r'(#+) ([^;]*) \(off-map\)', line)
                    if match:
                        off_map[len(match.group(1)) - 1].add(match.group(2))
    except FileNotFoundError:
        pass

    prev = None

    def write_line(f, line):
        nonlocal prev
        cur = line.split(';')[1] if ';' in line else '#'
        if prev != cur:
            print(file=f)
        print(line, file=f)
        prev = cur

    with open('province_table_new.csv', 'w', encoding='cp1252', newline='\r\n') as f:
        print('# CK2TITLE;EU4ID;Filename;Comment', file=f)
        for superregion_name, superregion in superregions.items():
            if localize[superregion_name] in off_map[0]:
                write_line(f, '# {} (off-map)'.format(localize[superregion_name]))
                continue
            write_line(f, '# {}'.format(localize[superregion_name]))
            for region_name in superregion:
                if localize[region_name] in off_map[1]:
                    write_line(f, '## {} (off-map)'.format(localize[region_name]))
                    continue
                write_line(f, '## {}'.format(localize[region_name]))
                for area_name in regions[region_name]:
                    if localize[area_name] in off_map[2]:
                        write_line(f, '### {} (off-map)'.format(localize[area_name]))
                        continue
                    write_line(f, '### {}'.format(localize[area_name]))
                    for province in areas[area_name]:
                        if names[province][0] in off_map[3]:
                            write_line(f, '#### {} (off-map)'.format(names[province][0]))
                            continue
                        if prov_mappings[province]:
                            seen = set()
                            for ck2title in prov_mappings[province]:
                                if ck2title in seen:
                                    comment = 'Duplicate to increase weight'
                                else:
                                    comment = ''
                                    if ck2title.startswith('d_'):
                                        comment += 'Duchy ' + ck2localize[ck2title]
                                    else:
                                        comment += ck2localize[title_key[ck2title]]
                                    comment += ' - ' + names[province][0]
                                    seen.add(ck2title)
                                write_line(f, '{};{};{};{}'.format(
                                    ck2title, province, history[province], comment))
                        else:
                            write_line(f, '####;{};{};{}'.format(
                                province, history[province], '/'.join(names[province])))


if __name__ == '__main__':
    main()
