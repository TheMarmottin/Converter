#!/usr/bin/env python3

import shutil
from ck2parser import (rootpath, SimpleParser, is_codename, Pair, csv_rows,
                       vanilladir)
from print_time import print_time

def ensure_empty(path):
    if path.exists():
        shutil.rmtree(str(path))
    path.mkdir(parents=True)

def build_cultures(parser, outdir):
    outdir /= 'common/cultures'
    ensure_empty(outdir)
    cultures = set()
    for path, tree in parser.parse_files('common/cultures/*'):
        if vanilladir in path.parents:
            continue
        diff = False
        for n, v in tree:
            for n2, v2 in v:
                if n2.val != 'graphical_cultures':
                    cultures.add(n2.val)
                    for p3 in reversed(v2.contents):
                        if p3.key.val == 'dynasty_title_names':
                            v2.contents.remove(p3)
                            diff = True
        if diff:
            parser.write(tree, outdir / path.name)
    return cultures

def build_landed_titles(parser, outdir, cultures, tagged_titles):
    outdir /= 'common/landed_titles'
    ensure_empty(outdir)
    for path, tree in parser.parse_files('common/landed_titles/*'):
        if vanilladir in path.parents or 'override' in path.name:
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

def copy_localisation(mods, outdir):
    outdir /= 'localisation'
    outdir.mkdir(parents=True, exist_ok=True)
    for path in outdir.glob('localisation/*.csv'):
        if path.name != 'converter.csv':
            path.unlink()
    for mod in mods:
        for path in mod.glob('localisation/*.csv'):
            shutil.copy(str(path), str(outdir / path.name))

@print_time
def main():
    swmh = rootpath / 'SWMH-BETA/SWMH'
    emf = rootpath / 'EMF/EMF'
    emf_swmh = rootpath / 'EMF/EMF+SWMH'
    mini = rootpath / 'MiniSWMH/MiniSWMH'
    sed = rootpath / 'sed2/build/SED2'
    sed_emf = rootpath / 'sed2/build/SED2+EMF'
    converter = rootpath / 'Converter/Converter'
    converter_mini = rootpath / 'Converter/Converter+Mini'
    parser = SimpleParser()

    tagged_titles = set()
    for title, *_ in csv_rows(converter / 'eu4_converter/nation_table.csv'):
        if title[0] in 'ekd':
            tagged_titles.add(title)

    parser.moddirs = [swmh, emf, emf_swmh]

    cultures = build_cultures(parser, converter)
    build_landed_titles(parser, converter, cultures, tagged_titles)
    parser.moddirs = [mini]
    build_landed_titles(parser, converter_mini, cultures, tagged_titles)

    copy_localisation([sed, sed_emf], converter)

if __name__ == '__main__':
    main()
