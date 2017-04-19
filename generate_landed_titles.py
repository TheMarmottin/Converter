#!/usr/bin/env python3

import ck2parser
import print_time

@print_time.print_time
def main():
    convdir = ck2parser.rootpath / 'Converter/Converter'
    moddirs = [ck2parser.rootpath / x for x in
               ['SWMH-BETA/SWMH', 'EMF/EMF', 'EMF/EMF+SWMH']]
    parser = ck2parser.SimpleParser(*moddirs)
    cultures = set(ck2parser.get_cultures(parser, groups=False))
    for path, tree in parser.parse_files('common/landed_titles/*'):
        diff = False
        dfs = list(tree)
        while dfs:
            n, v = dfs.pop()
            if ck2parser.is_codename(n.val):
                for p2 in reversed(v.contents):
                    if p2.key.val in cultures:
                        v.contents.remove(p2)
                        diff = True
                dfs.extend(v)
        if diff:
            outpath = convdir / 'common/landed_titles' / path.name
            if not outpath.parent.exists():
                outpath.parent.mkdir(parents=True)
            with outpath.open('w', encoding='cp1252', newline='\r\n') as f:
                f.write(tree.str(parser))

if __name__ == '__main__':
    main()
