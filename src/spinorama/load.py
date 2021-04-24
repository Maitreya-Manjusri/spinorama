#                                                  -*- coding: utf-8 -*-
import logging
import pandas as pd

from .compute_normalize import normalize_mean, normalize_cea2034, normalize_graph
from .compute_cea2034 import (
    early_reflections,
    vertical_reflections,
    horizontal_reflections,
    compute_cea2034,
    compute_onaxis,
    estimated_inroom_HV,
)

from .load_misc import graph_melt

logger = logging.getLogger("spinorama")


def load_normalize(df, ref_mean=None):
    # normalize all melted graphs
    dfc = {}
    mean = ref_mean
    if "CEA2034" in df:
        if ref_mean is None:
            mean = normalize_mean(df["CEA2034"])
            dfc["CEA2034_original_mean"] = mean
        for graph in df.keys():
            if graph != "CEA2034":
                if graph.replace("_unmelted", "") != graph:
                    dfc[graph] = df[graph]
                else:
                    dfc[graph] = normalize_graph(df[graph], mean)
        dfc["CEA2034"] = normalize_cea2034(df["CEA2034"], mean)
        logger.debug("mean for normalisation {0}".format(mean))
        return dfc
    if "On Axis" in df:
        if ref_mean is None:
            mean = normalize_mean(df["On Axis"])
            dfc["On Axis_original_mean"] = mean
        for graph in df.keys():
            if graph.replace("_unmelted", "") != graph:
                dfc[graph] = df[graph]
            else:
                dfc[graph] = normalize_graph(df[graph], mean)
        logger.debug("mean for normalisation {0}".format(mean))
        return dfc
    if ref_mean is not None:
        for graph in df.keys():
            if graph.replace("_unmelted", "") != graph:
                dfc[graph] = df[graph]
            else:
                dfc[graph] = normalize_graph(df[graph], mean)
        logger.debug("mean for normalisation {0}".format(mean))
        return dfc

    # do nothing
    logger.debug(
        "CEA2034 and On Axis are not in df knows keys are {0}".format(df.keys())
    )
    return df


def filter_graphs(speaker_name, h_spl, v_spl):
    dfs = {}
    # add H and V SPL graphs
    if h_spl is not None:
        dfs["SPL Horizontal_unmelted"] = h_spl
        dfs["SPL Horizontal"] = graph_melt(h_spl)
    else:
        logger.warning("h_spl is None for speaker {}".format(speaker_name))
    if v_spl is not None:
        dfs["SPL Vertical_unmelted"] = v_spl
        dfs["SPL Vertical"] = graph_melt(v_spl)
    else:
        logger.warning("v_spl is None for speaker {}".format(speaker_name))
    # add computed graphs
    table = [
        ["Early Reflections", early_reflections],
        ["Horizontal Reflections", horizontal_reflections],
        ["Vertical Reflections", vertical_reflections],
        ["Estimated In-Room Response", estimated_inroom_HV],
        ["On Axis", compute_onaxis],
        ["CEA2034", compute_cea2034],
    ]
    if h_spl is None or v_spl is None:
        #
        df = compute_onaxis(h_spl, v_spl)
        dfs["On Axis_unmelted"] = df
        dfs["On Axis"] = graph_melt(df)
        # SPL H
        if h_spl is not None:
            df = horizontal_reflections(h_spl, v_spl)
            dfs["Horizontal Reflections_unmelted"] = df
            dfs["Horizontal Reflections"] = graph_melt(df)
        # SPL V
        if v_spl is not None:
            df = vertical_reflections(h_spl, v_spl)
            dfs["Vectical Reflections_unmelted"] = df
            dfs["Vectical Reflections"] = graph_melt(df)
        # that's all folks
        return dfs

    for title, functor in table:
        try:
            df = functor(h_spl, v_spl)
            if df is not None:
                dfs[title + "_unmelted"] = df
                dfs[title] = graph_melt(df)
            else:
                logger.info(
                    "{0} computation is None for speaker{1:s}".format(
                        title, speaker_name
                    )
                )
        except KeyError as ke:
            logger.warning(
                "{0} computation failed with key:{1} for speaker{2:s}".format(
                    title, ke, speaker_name
                )
            )
    return dfs
