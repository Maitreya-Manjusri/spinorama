#!/usr/bin/env python3
#                                                  -*- coding: utf-8 -*-
# A library to display spinorama charts
#
# Copyright (C) 2020 Pierre Aubert pierreaubert(at)yahoo(dot)fr
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
usage: update-docs.py [--help] [--version] [--dev]\
 [--width=<width>] [--height=<height>] [--force] [--type=<ext>]\
 [--sitedev=<http>]

Options:
  --help            display usage()
  --version         script version number
  --width=<width>   width size in pixel
  --height=<height> height size in pixel
  --force           force regeneration of all graphs, by default only generate new ones
  --type=<ext>      choose one of: json, html, png, svg
  --sitedev=<http>  default: http://localhost:8000/docs
"""
import os
import sys
import json
from mako.template import Template
from mako.lookup import TemplateLookup
from src.spinorama.load import parse_all_speakers
from src.spinorama.analysis import estimates
import datas.metadata as metadata
from generate_graphs import generate_graphs
from docopt import docopt
from src.spinorama.path import name2measurement, measurement2name

siteprod = 'https://pierreaubert.github.io/spinorama'
sitedev = 'http://localhost:8000/docs/'


def sanity_check(df, meta):
    for measurement, graph in df.items():
        # check if metadata exists
        (speaker, origin) = name2measurement(measurement)
        if speaker not in meta:
            print('Fatal: Metadata not found for >', measurement, '<')
            return 1
        # check if image exists
        if not os.path.exists('datas/originals/' + speaker + '.jpg'):
            print('Fatal: Image associated with >', speaker, '< not found!')
            return 1
        # check if downscale image exists
        if not os.path.exists('docs/metadata/' + speaker + '.jpg'):
            print('Fatal: Image associated with >', speaker, '< not found!')
            print('Please run: cd docs && ./convert.sh')
            return 1
    return 0


def add_estimates(df):
    """""Compute some values per speaker and add them to metadata """
    for k, v in df.items():
        try:
            if 'CEA2034' in df[k].keys():
                spin = df[k]['CEA2034']
                if spin is not None:
                    onaxis = spin.loc[spin['Measurements'] == 'On Axis']
                    (speaker, title) = name2measurement(k)
                    metadata.speakers_info[speaker]['estimates'] = estimates(onaxis)
        except ValueError:
            print('Warning: Computing estimates failed for speaker: ' + k)


def generate_speaker(mako, df):
    speaker_html = mako.get_template('speaker.html')
    for speaker, measurements in df.items():
        with open('docs/' + speaker + '.html', 'w') as f:
            freq_filter = [
                "CEA2034",
                "Early Reflections",
                "Estimated In-Room Response",
                "Horizontal Reflections",
                "Vertical Reflections",
                "SPL Horizontal",
                "SPL Vertical"
            ]
            freqs = {key: measurements[key]
                     for key in freq_filter if key in measurements}
            contour_filter = [
                "SPL Horizontal_unmelted",
                "SPL Vertical_unmelted"
            ]
            contours = {key: measurements[key]
                        for key in contour_filter if key in measurements}
            radar_filter = [
                "SPL Horizontal_unmelted",
                "SPL Vertical_unmelted"
            ]
            radars = {key: measurements[key]
                      for key in radar_filter if key in measurements}
            f.write(speaker_html.render(speaker=speaker,
                                        freqs=freqs,
                                        contours=contours,
                                        radars=radars,
                                        meta=metadata.speakers_info,
                                        site=site))
            f.close()
    return 0


def dump_metadata(meta):
    def flatten(d):
        f = {}
        for k, v in d.items():
            s = {}
            for m in v['measurements']:
                for k2, v2 in v.items():
                    if k2 != 'measurements':
                        s[k2] = v2
                f[measurement2name(k, m)] = s
        return f

    with open('docs/assets/metadata.json', 'w') as f:
        meta = flatten(metadata.speakers_info)
        js = json.dumps(meta)
        f.write(js)
        f.close()
        return meta
    return None


if __name__ == '__main__':
    args = docopt(__doc__,
                  version='update-docs.py version 1.1',
                  options_first=True)

    # check args section
    width = 600
    height = 200
    force = args['--force']
    ptype = None

    if args['--width'] is not None:
        width = int(args['--width'])

    if args['--height'] is not None:
        height = int(args['--height'])

    if args['--type'] is not None:
        ptype = args['--type']
        if type not in ('png', 'html', 'svg', 'json'):
            print('type %s is not recognize!'.format(ptype))
            exit(1)

    dev = args['--dev']
    site = siteprod
    if dev is True:
        if args['--sitedev'] is not None:
            sitedev = args['--sitedev']
            if len(sitedev) < 4 or sitedev[0:4] != 'http':
                print('sitedev %s does not start with http!'.format(sitedev))
                exit(1)

        site = sitedev

    # read data from disk
    df = parse_all_speakers(metadata.speakers_info)
    if sanity_check(df, metadata.speakers_info) != 0:
        sys.exit(1)

    # add computed data to metadata
    add_estimates(df)

    # configure Mako
    mako_templates = TemplateLookup(directories=['templates'], module_directory='/tmp/mako_modules')

    # write metadata in a json file for easy search
    metameasurements = dump_metadata(metadata.speakers_info)
    print(metameasurements)

    # write index.html
    index_html = mako_templates.get_template('index.html')
    with open('docs/index.html', 'w') as f:
        f.write(index_html.render(speakers=df, meta=metameasurements, site=site))
        f.close()

    # write help.html
    help_html = mako_templates.get_template('help.html')
    with open('docs/help.html', 'w') as f:
        f.write(help_html.render(speakers=df, meta=metadata.speakers_info, site=site))
        f.close()

    # write a file per speaker
    generate_speaker(mako_templates, df)

    for f in ['search.js', 'bulma.js', 'compare.js', 'tabs.js', 'spinorama.css']:
        file_ext = Template(filename='templates/assets/'+f)
        with open('docs/assets/'+f, 'w') as fd:
            fd.write(file_ext.render(site=site))
            fd.close()

    # generate potential missing graphs
    generate_graphs(df, width, height, force, ptype)

    sys.exit(0)
