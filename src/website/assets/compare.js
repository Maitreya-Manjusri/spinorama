// -*- coding: utf-8 -*-
// A library to display spinorama charts
//
// Copyright (C) 2020-23 Pierre Aubert pierreaubert(at)yahoo(dot)fr
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

/*global Plotly*/
/*eslint no-undef: "error"*/

import { urlSite } from './misc.js';
import {
    getMetadata,
    assignOptions,
    knownMeasurements,
    getAllSpeakers,
    getSpeakerData,
    setContour,
    setGlobe,
    setGraph,
    setCEA2034,
    setRadar,
    setSurface,
} from './common.js';

function updateVersion(metaSpeakers, speaker, selector, origin, version) {
    // update possible version(s) for matching speaker and origin
    // console.log('update version for ' + speaker + ' origin=' + origin + ' version=' + version)
    const versions = Object.keys(metaSpeakers[speaker].measurements);
    let matches = new Set();
    versions.forEach((val) => {
        const current = metaSpeakers[speaker].measurements[val];
        if (current.origin === origin || origin === '' || origin == null) {
            matches.add(val);
            matches.add(val + '_eq');
        }
    });
    const [first] = matches;
    let correct_version = null;
    if (version != null && matches.has(version)) {
        correct_version = version;
    } else if (selector.value != null && matches.has(selector.value)) {
        correct_version = selector.value;
    } else {
        correct_version = first;
    }
    assignOptions(Array.from(matches), selector, correct_version);
}

function updateOrigin(metaSpeakers, speaker, originSelector, versionSelector, origin, version) {
    // console.log('updateOrigin for ' + speaker + ' with origin ' + origin + ' version=' + version)
    const measurements = Object.keys(metaSpeakers[speaker].measurements);
    const origins = new Set();
    for (const key in measurements) {
        origins.add(metaSpeakers[speaker].measurements[measurements[key]].origin);
    }
    const [first] = origins;
    // console.log('updateOrigin found this possible origins: ' + origins.size + ' first=' + first)
    // origins.forEach(item => console.log('updateOrigin: ' + item))
    let correct_origin = null;
    if (origin != null && origins.has(origin)) {
        correct_origin = origin;
    } else {
        correct_origin = first;
    }
    assignOptions(Array.from(origins), originSelector, correct_origin);
    updateVersion(metaSpeakers, speaker, versionSelector, correct_origin, version);
}

getMetadata()
    .then((metadata) => {
        const urlCompare = urlSite + 'compare.html?';
        const nbSpeakers = 2;

        const queryString = window.location.search;
        const urlParams = new URLSearchParams(queryString);

        const plotContainer = document.querySelector('[data-num="0"');
        const plotSingleContainer = plotContainer.querySelector('.plotSingle');
        const plotDouble0Container = plotContainer.querySelector('.plotDouble0');
        const plotDouble1Container = plotContainer.querySelector('.plotDouble1');
        const formContainer = plotContainer.querySelector('.plotForm');
        const graphsSelector = formContainer.querySelector('#compare-select-graph');

        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;

        const [metaSpeakers, speakers] = getAllSpeakers(metadata);
        const initSpeakers = buildInitSpeakers(speakers, nbSpeakers);
        const initMeasurement = buildInitMeasurement();
        const initOrigins = buildInitOrigins(nbSpeakers);
        const initVersions = buildInitVersions(nbSpeakers);

        const speakersSelector = [];
        const originsSelector = [];
        const versionsSelector = [];
        const fieldsetOriginsSelector = [];
        const fieldsetVersionsSelector = [];

        function plot(measurement, speakersName, speakersGraph) {
            // console.log('plot: ' + speakersName.length + ' names and ' + speakersGraph.length + ' graphs')
            async function run() {
                Promise.all(speakersGraph).then((graphs) => {
                    // console.log('plot: resolved ' + graphs.length + ' graphs')
                    let graphsConfigs = [];
                    if (measurement === 'CEA2034') {
                        graphsConfigs = setCEA2034(speakersName, graphs, windowWidth, windowHeight);
                    } else if (
                        measurement === 'On Axis' ||
                        measurement === 'Estimated In-Room Response' ||
                        measurement === 'Early Reflections' ||
                        measurement === 'SPL Horizontal' ||
                        measurement === 'SPL Vertical' ||
                        measurement === 'SPL Horizontal Normalized' ||
                        measurement === 'SPL Vertical Normalized' ||
                        measurement === 'Horizontal Reflections' ||
                        measurement === 'Vertical Reflections'
                    ) {
                        graphsConfigs = setGraph(speakersName, graphs, windowWidth, windowHeight);
                    } else if (measurement === 'SPL Horizontal Radar' || measurement === 'SPL Vertical Radar') {
                        graphsConfigs = setRadar(speakersName, graphs, windowWidth, windowHeight);
                    } else if (
                        measurement === 'SPL Horizontal Contour' ||
                        measurement === 'SPL Vertical Contour' ||
                        measurement === 'SPL Horizontal Contour Normalized' ||
                        measurement === 'SPL Vertical Contour Normalized'
                    ) {
                        graphsConfigs = setContour(speakersName, graphs, windowWidth, windowHeight);
                    } else if (
                        measurement === 'SPL Horizontal Contour 3D' ||
                        measurement === 'SPL Vertical Contour 3D' ||
                        measurement === 'SPL Horizontal Contour 3D Normalized' ||
                        measurement === 'SPL Vertical Contour 3D Normalized'
                    ) {
                        graphsConfigs = setSurface(speakersName, graphs, windowWidth, windowHeight);
                    } else if (
                        measurement === 'SPL Horizontal Globe' ||
                        measurement === 'SPL Vertical Globe' ||
                        measurement === 'SPL Horizontal Globe Normalized' ||
                        measurement === 'SPL Vertical Globe Normalized'
                    ) {
                        graphsConfigs = setGlobe(speakersName, graphs, windowWidth, windowHeight);
                    }

                    // console.log('datas and layouts length='+graphsConfigs.length)
                    if (graphsConfigs.length === 1) {
                        plotSingleContainer.style.display = 'block';
                        plotDouble0Container.style.display = 'none';
                        plotDouble1Container.style.display = 'none';
                        const config = graphsConfigs[0];
                        if (config) {
                            Plotly.newPlot('plotSingle', config);
                        }
                    } else if (graphsConfigs.length === 2) {
                        plotSingleContainer.style.display = 'none';
                        plotDouble0Container.style.display = 'block';
                        plotDouble1Container.style.display = 'block';
                        for (let i = 0; i < graphsConfigs.length; i++) {
                            const config = graphsConfigs[i];
                            if (config) {
                                Plotly.newPlot('plotDouble' + i, config);
                            }
                        }
                    }
                    return null;
                });
            }
            run();
        }

        function buildInitSpeakers(speakers, count) {
            const list = [];
            for (let pos = 0; pos < count; pos++) {
                if (urlParams.has('speaker' + pos)) {
                    list[pos] = urlParams.get('speaker' + pos);
                } else {
                    list[pos] = speakers[Math.floor(Math.random() * speakers.length)];
                }
            }
            return list;
        }

        function buildInitMeasurement() {
            if (urlParams.has('measurement')) {
                const m = urlParams.get('measurement');
                if (knownMeasurements.includes(m)) {
                    return m;
                }
            }
            return knownMeasurements[0];
        }

        function buildInitOrigins(count) {
            const list = [];
            for (let pos = 0; pos < count; pos++) {
                if (urlParams.has('origin' + pos)) {
                    list[pos] = urlParams.get('origin' + pos);
                } else {
                    list[pos] = null;
                }
            }
            return list;
        }

        function buildInitVersions(count) {
            const list = [];
            for (let pos = 0; pos < count; pos++) {
                if (urlParams.has('version' + pos)) {
                    list[pos] = urlParams.get('version' + pos);
                } else {
                    list[pos] = null;
                }
            }
            return list;
        }

        function updateTitle() {
            let title = 'Spinorama: compare ' + graphsSelector.value + ' graphs for speakers ';
            for (let i = 0; i < nbSpeakers; i++) {
                title += speakersSelector[i].value + ' (' + originsSelector[i].value + ') ';
                if (i < nbSpeakers - 1) {
                    title += ' v.s. ';
                }
            }
            document.title = title;
        }

        function updateSpeakers() {
            const names = [];
            const graphs = [];
            for (let i = 0; i < nbSpeakers; i++) {
                graphs[i] = getSpeakerData(
                    metaSpeakers,
                    graphsSelector.value,
                    speakersSelector[i].value,
                    originsSelector[i].value,
                    versionsSelector[i].value
                );
                names[i] = speakersSelector[i].value;
            }
            urlParams.set('measurement', graphsSelector.value);
            updateTitle();
            window.history.pushState({ page: 1 }, 'Change measurement', urlCompare + urlParams.toString());
            plot(graphsSelector.value, names, graphs);
        }

        function updateSpeakerPos(pos) {
            // console.log('updateSpeakerPos(' + pos + ')')
            updateOrigin(metaSpeakers, speakersSelector[pos].value, originsSelector[pos], versionsSelector[pos]);
            urlParams.set('speaker' + pos, speakersSelector[pos].value);
            updateOriginPos(pos);
        }

        function updateOriginPos(pos) {
            // console.log('updateOriginPos(' + pos + ')')
            updateOrigin(
                metaSpeakers,
                speakersSelector[pos].value,
                originsSelector[pos],
                versionsSelector[pos],
                originsSelector[pos].value
            );
            if (originsSelector[pos].childElementCount === 1) {
                fieldsetOriginsSelector[pos].disabled = true;
            } else {
                fieldsetOriginsSelector[pos].removeAttribute('disabled');
            }
            urlParams.set('origin' + pos, originsSelector[pos].value);
            updateVersionPos(pos);
        }

        function updateVersionPos(pos) {
            // console.log('updateVersionsPos(' + pos + ')')
            updateVersion(
                metaSpeakers,
                speakersSelector[pos].value,
                versionsSelector[pos],
                originsSelector[pos].value,
                versionsSelector[pos].value
            );
            if (versionsSelector[pos].childElementCount === 1) {
                fieldsetVersionsSelector[pos].disabled = true;
            } else {
                fieldsetVersionsSelector[pos].removeAttribute('disabled');
            }
            urlParams.set('version' + pos, versionsSelector[pos].value);
            window.history.pushState({ page: 1 }, 'Compare speakers', urlCompare + urlParams.toString());
        }

        // initial setup
        for (let pos = 0; pos < nbSpeakers; pos++) {
            const tpos = pos.toString();
            speakersSelector[pos] = formContainer.querySelector('#compare-select-speaker' + tpos);
            originsSelector[pos] = formContainer.querySelector('#compare-select-origin' + tpos);
            versionsSelector[pos] = formContainer.querySelector('#compare-select-version' + tpos);
            fieldsetOriginsSelector[pos] = formContainer.querySelector('#compare-fieldset-origin' + tpos);
            fieldsetVersionsSelector[pos] = formContainer.querySelector('#compare-fieldset-version' + tpos);
        }

        for (let pos = 0; pos < nbSpeakers; pos++) {
            assignOptions(speakers, speakersSelector[pos], initSpeakers[pos]);
        }
        assignOptions(knownMeasurements, graphsSelector, initMeasurement);

        const initDatas = [];
        for (let pos = 0; pos < nbSpeakers; pos++) {
            updateOrigin(metaSpeakers, initSpeakers[pos], originsSelector[pos], versionsSelector[pos], null, null);
            updateSpeakerPos(pos);
            // console.log('DEBUG: ' + originsSelector[pos].options[0])
            initDatas[pos] = getSpeakerData(
                metaSpeakers,
                initMeasurement,
                initSpeakers[pos],
                initOrigins[pos],
                initVersions[pos]
            );
        }
        updateSpeakers();

        // add listeners
        graphsSelector.addEventListener('change', updateSpeakers, false);

        document.addEventListener('keydown', (event) => {
            const key = event.key;
            if (key === 'a' || key === '1') {
                speakersSelector[0].focus();
            } else if (key === 'b' || key === '2') {
                speakersSelector[1].focus();
            } else if (key === 'g') {
                graphsSelector.focus();
            }
        });

        for (let pos = 0; pos < nbSpeakers; pos++) {
            speakersSelector[pos].addEventListener(
                'change',
                () => {
                    updateSpeakerPos(pos);
                    updateSpeakers();
                },
                false
            );
            originsSelector[pos].addEventListener(
                'change',
                () => {
                    updateOriginPos(pos);
                    updateSpeakers();
                },
                false
            );
            versionsSelector[pos].addEventListener(
                'change',
                () => {
                    updateVersionPos(pos);
                    updateSpeakers();
                },
                false
            );
        }

        plot(initMeasurement, initSpeakers, initDatas);
    })
    .catch((err) => console.log(err.message));
