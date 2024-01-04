#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# A library to display spinorama charts
#
# Copyright (C) 2020-2023 Pierre Aubert pierre(at)spinorama(dot)org
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
usage: generate_html.py [--help] [--version] [--dev]\
 [--sitedev=<http>]  [--log-level=<level>]

Options:
  --help            display usage()
  --version         script version number
  --sitedev=<http>  default: http://localhost:8000/docs
  --log-level=<level> default is WARNING, options are DEBUG INFO ERROR.
"""
from glob import glob
import json
import os
import shutil
import subprocess
import pathlib
import sys

from docopt import docopt

from mako.lookup import TemplateLookup

from datas.metadata import speakers_info as extradata
from generate_common import (
    args2level,
    get_custom_logger,
    find_metadata_file,
    find_metadata_file_chunks,
    sort_metadata_per_score,
    sort_metadata_per_date,
)

import spinorama.constant_paths as cpaths
from spinorama.need_update import need_update

SITEPROD = "https://www.spinorama.org"
SITEDEV = "https://dev.spinorama.org"


def write_if_different(new_content: str, filename: str, force: bool):  # noqa: FBT001
    """Write the new content to disk only if it is different from the current one.
    The unchanged html files are then untouched and http cache effect is better.
    """
    identical = False
    path = pathlib.Path(filename)
    if path.exists():
        old_content = path.read_text(encoding="utf-8")
        if old_content == new_content:
            identical = True

    if not identical or force:
        path.write_text(new_content, encoding="utf-8")


FREQ_FILTER = [
    "CEA2034",
    "On Axis",
    "Early Reflections",
    "Estimated In-Room Response",
    "Horizontal Reflections",
    "Vertical Reflections",
    "SPL Horizontal",
    "SPL Vertical",
    "SPL Horizontal Normalized",
    "SPL Vertical Normalized",
]

CONTOUR_FILTER = [
    "SPL Horizontal Contour",
    "SPL Vertical Contour",
    "SPL Horizontal Contour Normalized",
    "SPL Vertical Contour Normalized",
    "SPL Horizontal Contour 3D",
    "SPL Vertical Contour 3D",
    "SPL Horizontal Contour Normalized 3D",
    "SPL Vertical Contour Normalized 3D",
]

RADAR_FILTER = [
    "SPL Horizontal Radar",
    "SPL Vertical Radar",
]


def generate_measurement(
    dataframe,
    meta,
    site,
    use_search,
    speaker_name,
    origins,
    speaker_html,
    graph_html,
    origin,
    measurements,
    key,
    dfs,
):
    logger.debug("generate %s %s %s", speaker_name, origin, key)
    freq = {k: dfs[k] for k in FREQ_FILTER if k in dfs}
    contour = {k: dfs[k] for k in CONTOUR_FILTER if k in dfs}
    radar = {k: dfs[k] for k in RADAR_FILTER if k in dfs}
    # eq
    eq = None
    if key != "default_eq":
        eq_filter = [
            "ref_vs_eq",
        ]
    eq = {k: dfs[k] for k in eq_filter if k in dfs}
    # get index.html filename
    dirname = "{}/{}/".format(cpaths.CPATH_DOCS_SPEAKERS, speaker_name)
    if origin in ("ASR", "Princeton", "ErinsAudioCorner", "Misc"):
        dirname += origin
    else:
        dirname += meta[speaker_name]["brand"]
    index_name = "{0}/index_{1}.html".format(dirname, key)

    # write index.html
    logger.info("Writing %s for %s", index_name, speaker_name)
    speaker_content = speaker_html.render(
        speaker=speaker_name,
        g_freq=freq,
        g_contour=contour,
        g_radar=radar,
        g_key=key,
        g_eq=eq,
        meta=meta,
        origin=origin,
        site=site,
        use_search=use_search,
    )
    index_deps = [
        "./src/website/speaker.html",
        "./src/website/speaker_desc.html",
        "./src/website/utils.py",
        "./datas/metadata.py",
        find_metadata_file(),
        # *find_metadata_file_chunks(),
        *glob("./src/website/assets/*.js"),
    ]
    index_force = need_update(index_name, index_deps)
    write_if_different(speaker_content, index_name, index_force)

    # write a small file per graph to render the json generated by Vega
    for kind in [freq, contour, radar]:
        for graph_name in kind:
            graph_filename = "{0}/{1}/{2}.html".format(dirname, key, graph_name)
            logger.info("Writing %s/%s for %s", key, graph_filename, speaker_name)
            graph_content = graph_html.render(
                speaker=speaker_name, graph=graph_name, meta=meta, site=site
            )
            graph_deps = [
                *glob("./datas/measurements/{}/{}/*.*".format(speaker_name, key)),
                *glob("./src/spinorama/*.py"),
            ]
            graph_force = need_update(graph_filename, graph_deps)
            write_if_different(graph_content, graph_filename, graph_force)


def generate_speaker(
    dataframe, meta, site, use_search, speaker_name, origins, speaker_html, graph_html
):
    for origin, measurements in origins.items():
        for key, dfs in measurements.items():
            try:
                # print('DEBUG: '+speaker_name+' origin='+origin+' version='+key)
                generate_measurement(
                    dataframe,
                    meta,
                    site,
                    use_search,
                    speaker_name,
                    origins,
                    speaker_html,
                    graph_html,
                    origin,
                    measurements,
                    key,
                    dfs,
                )
            except KeyError as key_error:
                print(
                    "generate_speaker: a file per speaker for {} failed with {}".format(
                        speaker_name, key_error
                    )
                )


def generate_speakers(mako, dataframe, meta, site, use_search):
    """For each speaker, generates a set of HTML files driven by templates"""
    speaker_html = mako.get_template("speaker.html")
    graph_html = mako.get_template("graph.html")
    for speaker_name, origins in dataframe.items():
        logger.debug("html generation for speaker_name %s", speaker_name)
        if speaker_name in extradata and extradata[speaker_name].get("skip", False):
            logger.debug("skipping %s", speaker_name)
            continue
        generate_speaker(
            dataframe, meta, site, use_search, speaker_name, origins, speaker_html, graph_html
        )

    return 0


def main():
    # load all metadata from generated json file
    json_filename = find_metadata_file()
    if json_filename is None:
        logger.error("Cannot find %s", json_filename)
        sys.exit(1)

    meta = None
    with open(json_filename, "r") as f:
        meta = json.load(f)

    # only build a dictionnary will all graphs
    main_df = {}
    speakers = glob("{}/*".format(cpaths.CPATH_DOCS_SPEAKERS))
    for speaker in speakers:
        if not os.path.isdir(speaker):
            continue
        # humm annoying
        speaker_name = speaker.replace(cpaths.CPATH_DOCS_SPEAKERS + "/", "")
        if speaker_name in ("score", "assets", "stats", "compare", "logos", "pictures"):
            continue
        main_df[speaker_name] = {}
        origins = glob(speaker + "/*")
        for origin in origins:
            if not os.path.isdir(origin):
                continue
            origin_name = os.path.basename(origin)
            main_df[speaker_name][origin_name] = {}
            defaults = glob(origin + "/*")
            for default in defaults:
                if not os.path.isdir(default):
                    continue
                default_name = os.path.basename(default)
                main_df[speaker_name][origin_name][default_name] = {}
                graphs = glob(default + "/*_large.png")
                for graph in graphs:
                    g = os.path.basename(graph).replace("_large.png", "")
                    main_df[speaker_name][origin_name][default_name][g] = {}

    # configure Mako
    mako_templates = TemplateLookup(
        directories=["src/website"], module_directory="./build/mako_modules"
    )

    # write index.html
    logger.info("Write index.html")
    index_html = mako_templates.get_template("index.html")
    meta_sorted_date = sort_metadata_per_date(meta)

    try:
        html_content = index_html.render(
            df=main_df, meta=meta_sorted_date, site=site, use_search=True
        )
        html_filename = f"{cpaths.CPATH_DOCS}/index.html"
        write_if_different(html_content, html_filename, force=False)
    except KeyError as key_error:
        print("Generating index.html failed with {}".format(key_error))
        sys.exit(1)

    # write eqs.html
    logger.info("Write eqs.html")
    eqs_html = mako_templates.get_template("eqs.html")

    try:
        eqs_content = eqs_html.render(df=main_df, meta=meta_sorted_date, site=site, use_search=True)
        eqs_filename = f"{cpaths.CPATH_DOCS}/eqs.html"
        write_if_different(eqs_content, eqs_filename, force=False)
    except KeyError as key_error:
        print("Generating eqs.htmlfailed with {}".format(key_error))
        sys.exit(1)

    # write various html files
    meta_sorted_score = sort_metadata_per_score(meta)
    try:
        for item in (
            "scores",
            "help",
            "compare",
            "statistics",
            "similar",
        ):
            item_name = "{0}.html".format(item)
            logger.info("Write %s", item_name)
            item_html = mako_templates.get_template(item_name)
            use_search = False
            if item in ("scores", "similar"):
                use_search = True
            item_content = item_html.render(
                df=main_df, meta=meta_sorted_score, site=site, use_search=use_search
            )
            item_filename = cpaths.CPATH_DOCS + "/" + item_name
            write_if_different(item_content, item_filename, force=False)

    except KeyError as key_error:
        print("Generating various html files failed with {}".format(key_error))
        sys.exit(1)

    # write a file per speaker
    logger.info("Write a file per speaker")
    try:
        generate_speakers(mako_templates, main_df, meta=meta, site=site, use_search=False)
    except KeyError as key_error:
        print("Generating a file per speaker failed with {}".format(key_error))
        sys.exit(1)

    # copy favicon(s)
    for f in [
        "favicon.ico",
        "favicon-16x16.png",
    ]:
        file_in = cpaths.CPATH_DATAS_LOGOS + "/" + f
        file_out = cpaths.CPATH_DOCS + "/" + f
        shutil.copy(file_in, file_out)

    for f in [
        "spinorama.css",
    ]:
        file_in = cpaths.CPATH_WEBSITE_ASSETS_CSS + "/" + f
        file_out = cpaths.CPATH_DOCS_ASSETS_CSS + "/" + f
        shutil.copy(file_in, file_out)

    flow_bin = "flow-remove-types"
    flow_param = ""  # "--pretty --sourcemaps"

    flow_command = "{} {} {} {} {}".format(
        flow_bin,
        flow_param,
        cpaths.CPATH_WEBSITE_ASSETS_JS,
        "--out-dir",
        cpaths.CPATH_DOCS_ASSETS_JS,
    )
    status = subprocess.run(
        [flow_command], shell=True, check=True, capture_output=True  # noqa: S602
    )
    if status.returncode != 0:
        print("flow failed")

    # copy css/js files
    logger.info("Copy js files to %s", cpaths.CPATH_DOCS_ASSETS_JS)
    try:
        for item in (
            "misc",
            "meta",
            "params",
        ):
            item_name = "assets/{0}.js".format(item)
            logger.info("Write %s", item_name)
            item_html = mako_templates.get_template(item_name)
            # remove the ./docs/assets parts
            metadata_filename = json_filename[13:]
            item_content = item_html.render(
                df=main_df, meta=meta_sorted_score, site=site, metadata_filename=metadata_filename
            )
            item_filename = cpaths.CPATH_DOCS + "/" + item_name
            write_if_different(item_content, item_filename, force=False)
    except KeyError as key_error:
        print("Generating various html files failed with {}".format(key_error))
        sys.exit(1)

    # generate robots.txt and sitemap.xml
    logger.info("Copy robots/sitemap files to %s", cpaths.CPATH_DOCS)
    try:
        for item_name in (
            "robots.txt",
            "sitemap.xml",
        ):
            logger.info("Write %s", item_name)
            item_html = mako_templates.get_template(item_name)
            item_content = item_html.render(
                df=main_df, meta=meta_sorted_score, site=site, isProd=(site == SITEPROD)
            )
            item_filename = cpaths.CPATH_DOCS + "/" + item_name
            # ok for robots but likely doesn't work for sitemap
            write_if_different(item_content, item_filename, force=False)
    except KeyError as key_error:
        print("Generating various html files failed with {}".format(key_error))
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    args = docopt(__doc__, version="update_html.py version 1.23", options_first=True)
    dev = args["--dev"]
    site = SITEPROD
    if dev is True:
        site = SITEDEV
        if args["--sitedev"] is not None:
            site = args["--sitedev"]
            if len(site) < 4 or site[0:4] != "http":
                print("sitedev {} does not start with http!".format(site))
                sys.exit(1)

    logger = get_custom_logger(level=args2level(args), duplicate=True)
    main()
