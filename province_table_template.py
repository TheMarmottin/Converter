#!/usr/bin/env python3

import collections
import csv
import pathlib
import re
import ck2parser
import localpaths
import print_time


@print_time.print_time
def main():
    parser = ck2parser.SimpleParser(ck2parser.rootpath / 'SWMH-BETA/SWMH')
    ck2localize = ck2parser.get_localisation(parser.moddirs)
    title_key = {title: 'PROV{}'.format(prov)
                 for prov, title, _ in ck2parser.get_provinces(parser)}
    parser.moddirs = []

    eu4root = localpaths.eu4dir
    localize = {}
    for path in (eu4root / 'localisation').glob('*_l_english.yml'):
        with path.open(encoding='utf-8-sig') as f:
            for line in f:
                match = re.fullmatch(r'\s*([^#\s:]+):\d?\s*"(.*)"[^"]*', line)
                if match:
                    localize[match.group(1)] = match.group(2)
    areas = {}
    regions = collections.OrderedDict()
    superregions = collections.OrderedDict()
    for n, v in parser.parse_file(eu4root / 'map/area.txt'):
        areas[n.val] = [v2.val for v2 in v if isinstance(v2, ck2parser.Number)]
    with (eu4root / 'map/region.txt').open(encoding='cp1252') as f:
        # klugey
        region_text = f.read().split('#Sea Regions', 1)[0]
    for n, v in parser.parse(region_text):
        if v.contents:
            regions[n.val] = [v3.val for _, v2 in v for v3 in v2]
    for n, v in parser.parse_file(eu4root / 'map/superregion.txt'):
        if v.contents:
            superregions[n.val] = [v2.val for v2 in v]
    orphan_regions = [rn for rn, rv in regions.items()
                      if not any(rn in srv for srv in superregions.values())]
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

    off_map = [set(), set(), set(), set()]
    prov_mappings = collections.defaultdict(list)
    errors = set()
    unmapped_counties = set(title_key)
    try:
        with open('province_table.csv', encoding='cp1252') as f:
            for line in f:
                match = re.match(r'([^#;]*);([^#;]*)', line)
                if match:
                    ck2title = match.group(1)
                    eu4id = int(match.group(2))
                    if (ck2title not in title_key and
                        ck2title not in ck2localize):
                        errors.add(ck2title)
                    unmapped_counties.discard(ck2title)
                    prov_mappings[eu4id].append(ck2title)
                else:
                    match = re.match(r'(#+) ([^;]*) \(off-map\)', line)
                    if match:
                        off_map[len(match.group(1)) - 1].add(match.group(2))
    except FileNotFoundError:
        pass

    if errors:
        print('Invalid titles:')
        print(*sorted(errors))
        raise SystemExit()

    # expected unmapped counties:
    # 	c_ainazawa c_djanet c_elgolea c_ghat c_hoggar c_idjil c_ilizi c_masin
    # 	c_ouadane c_roufra c_tagant c_tazerbo c_tindouf c_tuat c_wallen

    if unmapped_counties:
        print('Unmapped counties:')
        print(*sorted(unmapped_counties))

    prev = None

    def write_line(line):
        nonlocal prev
        cur = line.split(';')[1] if ';' in line else '#'
        if prev != cur:
            print(file=f)
        print(line, file=f)
        prev = cur

    def write_region(region_name):
        if localize[region_name] in off_map[1]:
            write_line('## {} (off-map)'.format(localize[region_name]))
            return
        write_line('## {}'.format(localize[region_name]))
        for area_name in regions[region_name]:
            # unlocalized ad_dahna_area etc.
            localize[area_name] = localize.get(area_name, area_name)
            if localize[area_name] in off_map[2]:
                write_line('### {} (off-map)'.format(localize[area_name]))
                continue
            write_line('### {}'.format(localize[area_name]))
            for province in areas[area_name]:
                if names[province][0] in off_map[3]:
                    write_line('#### {} (off-map)'.format(names[province][0]))
                    continue
                if prov_mappings[province]:
                    seen_title = set()
                    for ck2title in prov_mappings[province]:
                        if ck2title in seen_title:
                            comment = 'Duplicate to increase weight'
                        else:
                            comment = ''
                            if ck2title.startswith('d_'):
                                comment += 'Duchy ' + ck2localize[ck2title]
                            else:
                                comment += ck2localize[title_key[ck2title]]
                            comment += ' - ' + names[province][0]
                            seen_title.add(ck2title)
                        write_line('{};{};{};{}'.format(
                            ck2title, province, history[province], comment))
                else:
                    write_line('####;{};{};{}'.format(province,
                               history[province], '/'.join(names[province])))

    with open('province_table.csv', 'w', encoding='cp1252',
              newline='\r\n') as f:
        print('# CK2TITLE;EU4ID;Filename;Comment', file=f)
        for region_name in orphan_regions:
            write_region(region_name)
        for superregion_name, superregion in superregions.items():
            if localize[superregion_name] in off_map[0]:
                write_line('# {} (off-map)'.format(localize[superregion_name]))
                continue
            write_line('# {}'.format(localize[superregion_name]))
            for region_name in superregion:
                write_region(region_name)


if __name__ == '__main__':
    main()
