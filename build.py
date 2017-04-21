#!/usr/bin/env python3

import shutil
from ck2parser import (rootpath, SimpleParser, get_cultures, is_codename, Pair,
                       csv_rows)
from print_time import print_time

def ensure_empty(path):
    if path.exists():
        shutil.rmtree(str(path))
    path.mkdir(parents=True)

def build_landed_titles(parser, mod, tagged_titles):
    outdir = (rootpath / ('Converter/Converter+' + mod.name) /
              'common/landed_titles')
    ensure_empty(outdir)
    parser.moddirs = [mod]
    cultures = set(get_cultures(parser, groups=False))
    for path, tree in parser.parse_files('common/landed_titles/*', mod):
        if 'override' in path.name:
            continue
        diff = False
        dfs = list(tree)
        while dfs:
            n, v = dfs.pop()
            if is_codename(n.val):
                for p2 in reversed(v.contents):
                    if p2.key.val in cultures:
                        v.contents.remove(p2)
                        diff = True
                dfs.extend(v)
                if (n.val in tagged_titles and
                    not v.has_pair('dynasty_title_names', 'no')):
                    v.contents.append(Pair('dynasty_title_names', 'no'))
                    diff = True
        if diff:
            parser.write(tree, outdir / path.name)

@print_time
def main():
    swmh = rootpath / 'SWMH-BETA/SWMH'
    emf = rootpath / 'EMF/EMF'
    emf_swmh = rootpath / 'EMF/EMF+SWMH'
    mini = rootpath / 'MiniSWMH/MiniSWMH'
    converter = rootpath / 'Converter'
    parser = SimpleParser()

    tagged_titles = set()
    nation_table = converter / 'Converter/eu4_converter/nation_table.csv'
    for title, *_ in csv_rows(nation_table):
        if title[0] in 'ekd':
            tagged_titles.add(title)

    build_landed_titles(parser, swmh, tagged_titles)
    build_landed_titles(parser, emf, tagged_titles)
    build_landed_titles(parser, emf_swmh, tagged_titles)

if __name__ == '__main__':
    main()
