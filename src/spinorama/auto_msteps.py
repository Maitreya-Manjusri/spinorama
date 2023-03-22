# -*- coding: utf-8 -*-
# A library to display spinorama charts
#
# Copyright (C) 2020-23 Pierre Aubert pierreaubert(at)yahoo(dot)fr
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

from spinorama.ltype import Peq, Vector, OptimResult
from spinorama import logger
from spinorama.auto_geq import optim_grapheq
from spinorama.auto_greedy import optim_greedy


def optim_multi_steps(
    speaker_name: str,
    df_speaker: dict,
    freq: Vector,
    auto_target: list[Vector],
    auto_target_interp: list[Vector],
    optim_config: dict,
    use_score,
) -> tuple[bool, tuple[OptimResult, Peq]]:
    """Implement multi steps optimisation:
    Start with a greedy approach then add another algorithm to optimise for score
    """
    if optim_config["use_grapheq"] is True:
        grapheq_status, (grapheq_results, grapheq_peq) = optim_grapheq(
            speaker_name,
            df_speaker,
            freq,
            auto_target,
            auto_target_interp,
            optim_config,
            use_score,
        )
        if grapheq_status is False:
            logger.info("autoEQ (GraphEQ) failed for %s", speaker_name)
        return grapheq_status, (grapheq_results, grapheq_peq)

    greedy_status, (greedy_results, greedy_peq) = optim_greedy(
        speaker_name,
        df_speaker,
        freq,
        auto_target,
        auto_target_interp,
        optim_config,
        use_score,
    )

    if greedy_status is False:
        logger.info("autoEQ (Greedy) failed for %s", speaker_name)

    if not use_score or not optim_config["second_optimiser"]:
        return greedy_status, (greedy_results, greedy_peq)

    return False, ((0, 0, 0), [])
