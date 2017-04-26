#!/usr/bin/env python3

import shutil
from ck2parser import (rootpath, SimpleParser, get_cultures, is_codename, Pair,
                       csv_rows, vanilladir)
from print_time import print_time

def ensure_empty(path):
    if path.exists():
        shutil.rmtree(str(path))
    path.mkdir(parents=True)

def build_landed_titles(parser, outdir, tagged_titles):
    outdir /= 'common/landed_titles'
    ensure_empty(outdir)
    cultures = set(get_cultures(parser, groups=False))
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
    build_landed_titles(parser, converter, tagged_titles)
    parser.moddirs = [mini]
    build_landed_titles(parser, converter_mini, tagged_titles)

    copy_localisation([sed, sed_emf], converter)

if __name__ == '__main__':
    main()
