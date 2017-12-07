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
    eu4root = localpaths.eu4dir
    converter = ck2parser.rootpath / 'Converter/Converter/eu4_converter'
    v_converter = ck2parser.rootpath / 'ck2-vanilla/dlc/dlc030/eu4_converter'
    swmh = ck2parser.rootpath / 'SWMH-BETA/SWMH'
    parser = ck2parser.SimpleParser(swmh)

    # # print SWMH_cultures
    # ck2localize = ck2parser.get_localisation([swmh])
    # with open('SWMH_cultures.txt', 'w', encoding='cp1252') as f:
    #    for _, tree in parser.parse_files('common/cultures/*'):
    #        for n, v in tree:
    #            print('{}({})'.format(n.val, ck2localize.get(n.val, '')),
    #                  file=f)
    #            for n2, v2 in v:
    #                if n2.val != 'graphical_cultures':
    #                    print('\t{}({})'.format(n2.val,
    #                                            ck2localize.get(n2.val, '')),
    #                          file=f)
    # # print EU4_cultures
    # eu4localize = {}
    # for folder in [eu4root, pathlib.Path('copy')]:
    #     for path in (folder / 'localisation').glob('*_l_english.yml'):
    #         with path.open(encoding='utf-8-sig') as f:
    #             for line in f:
    #                 match = re.fullmatch(r'\s*([^#\s:]+):\d?\s*"(.*)"[^"]*',
    #                                      line)
    #                 if match:
    #                     eu4localize[match.group(1)] = match.group(2)
    # not_cultures = ['dynasty_names', 'graphical_culture',
    #                 'second_graphical_culture', 'male_names', 'female_names']
    # with open('EU4_cultures.txt', 'w', encoding='cp1252') as f:
    #     for path in (eu4root / 'common/cultures').iterdir():
    #         for n, v in parser.parse_file(path):
    #             print('{}({})'.format(n.val, eu4localize.get(n.val, '')),
    #                   file=f)
    #             for n2, v2 in v:
    #                 if n2.val not in not_cultures:
    #                     print('\t{}({})'.format(n2.val,
    #                                             eu4localize.get(n2.val, '')),
    #                           file=f)
    # raise SystemExit()

    ck2cultures = ck2parser.get_cultures(parser, groups=False)
    parser.moddirs = []

    not_cultures = ['dynasty_names', 'graphical_culture',
                    'second_graphical_culture', 'male_names', 'female_names']
    cultures = []
    culture_groups = []
    group_of_culture = {}
    custom_cultures = set()
    for path in (eu4root / 'common/cultures').iterdir():
        for n, v in parser.parse_file(path):
            if n.val not in culture_groups:
                culture_groups.append(n.val)
            for n2, v2 in v:
                if n2.val not in not_cultures:
                    cultures.append(n2.val)
                    group_of_culture[n2.val] = n.val
    for folder in [v_converter, converter]:
        for path in (folder / 'common/cultures').iterdir():
            for n, v in parser.parse_file(path):
                if n.val not in culture_groups:
                    culture_groups.append(n.val)
                for n2, v2 in v:
                    if n2.val not in not_cultures:
                        cultures.append(n2.val)
                        group_of_culture[n2.val] = n.val
                        custom_cultures.add(n2.val)

    ck2localize = ck2parser.get_localisation([swmh])

    eu4localize = {}
    for folder in [eu4root, v_converter / 'copy']:
        for path in (folder / 'localisation').glob('*_l_english.yml'):
            with path.open(encoding='utf-8-sig') as f:
                for line in f:
                    match = re.fullmatch(r'\s*([^#\s:]+):\d?\s*"(.*)"[^"]*',
                                         line)
                    if match:
                        eu4localize[match.group(1)] = match.group(2)

    culture_table = []
    unmapped_cultures = list(ck2cultures)
    with (converter / 'culture_table.csv').open(encoding='cp1252') as f:
        for line in f:
            match = re.fullmatch(r'([^#;]*);([^#;]*);([^#;]*);([^;]*)\n',
                                 line)
            if match:
                ck2, eu4, custom, name = match.groups()
                if ck2 in unmapped_cultures:
                    if custom == '0':
                        if '#' in name:
                            name = (eu4localize[eu4] + ' # ' +
                                    name.split('#', maxsplit=1)[1].strip())
                        else:
                            name = eu4localize[eu4]
                    culture_table.append([ck2, eu4, custom, name])
                    unmapped_cultures.remove(ck2)

    culture_table.sort(key=lambda x: (
        culture_groups.index(group_of_culture[x[1]]),
        cultures.index(x[1]),
        ck2cultures.index(x[0])))

    with (converter / 'culture_table.csv').open('w', encoding='cp1252') as f:
        print('# CK2CULTURE;EU4CULTURE;Custom Defined;Comment', file=f)
        prev_group = None
        for row in culture_table:
            group = group_of_culture[row[1]]
            if group != prev_group:
                print('\n# {}\n'.format(eu4localize.get(group, group)), file=f)
            print(';'.join(row), file=f)
            prev_group = group
        if unmapped_cultures:
            print('\n# (unmapped)\n', file=f)
            for culture in unmapped_cultures:
                print('#{};;;;'.format(culture), file=f)


if __name__ == '__main__':
    main()
