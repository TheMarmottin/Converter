#!/usr/bin/env python3

import collections
import csv
import pathlib
import re
import ck2parser
import print_time


@print_time.print_time
def main():
    eu4root = pathlib.Path('/cygdrive/c/SteamLibrary/steamapps/common/Europa Universalis IV')
    parser = ck2parser.SimpleParser()
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
    localize = {}
    for path in (eu4root / 'localisation').glob('*_l_english.yml'):
        with path.open(encoding='utf-8-sig') as f:
            for line in f:
                match = re.fullmatch(r'\s*([^#\s:]+):\d?\s*"(.*)"[^"]*', line)
                if match:
                    localize[match.group(1)] = match.group(2)
    names = collections.defaultdict(set)
    for path in (eu4root / 'common/province_names').iterdir():
        with path.open() as f:
            for line in f:
                match = re.fullmatch(r' *(\d+) *= *"([^"]*)"', line)
                if match:
                    names[int(match.group(1))].add(match.group(2))
    for n, v in localize.items():
        if re.fullmatch(r'PROV\d+', n):
            num = int(n[4:])
            names[num].discard(v)
            names[num] = [v] + sorted(names[num])

    with open('province_table.csv', 'w') as f:
        f.write('# CK2TITLE;EU4ID;Filename;Comment\n\n')
        for superregion_name, superregion in superregions.items():
            f.write('# {}\n'.format(localize[superregion_name]))
            for region_name in superregion:
                f.write('## {}\n'.format(localize[region_name]))
                for area_name in regions[region_name]:
                    f.write('### {}\n\n'.format(localize[area_name]))
                    for province in areas[area_name]:
                        f.write(';{};{};{}\n\n'.format(province, history[province], '/'.join(names[province])))


if __name__ == '__main__':
    main()
