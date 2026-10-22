function alwaysFloatAxis(axisName) {
    return axis => (axis === axisName ? 'float' : null);
}


function parameterDrivenAxis(axisName, variableSelId, parametersSelId) {
    return function(axis) {
        if (axis !== axisName) {
            return null;
        }
        if (!parametersSelId) {
            return 'float';
        }
        const variable = $(`#${variableSelId}`).val();
        const paramKey = $(`#${parametersSelId}`).val();
        // const param = (typeof PARAMS_LIST !== 'undefined') && PARAMS_LIST[variable]?.[paramKey];
        // return param?.dtype === 'integer' ? { kind: 'integer', unit: param.unit } : 'float';
        const param = (typeof PARAMS_LIST !== 'undefined' && PARAMS_LIST[variable] != null) ? PARAMS_LIST[variable][paramKey] : undefined;
        return param != null && param.dtype === 'integer' ? { kind: 'integer', unit: param.unit } : 'float';
    };
}

function yearIndexAxis(axisName) {
    return axis => (axis === axisName ? 'year' : null);
}


function combineAxisResolvers(...resolvers) {
    return axis => {
        for (const resolver of resolvers) {
            const kind = resolver(axis);
            if (kind) {
                return kind;
            }
        }
        return null;
    };
}

function makeCaseKeyResolver(...selectIds) {
    /* beautify preserve:start */
    // return () => selectIds.map(id => $(`#${id}`).val() ?? '').join('|');
    /* beautify preserve:end */
    return () => selectIds
        .map(id => {
            const value = $(`#${id}`).val();
            return value == null ? '' : value;
        })
        .join('|');
}

function setAnalysisExpandModalRaw(tempRes, contID) {
    showModalDialog(`modal-expand-${contID}`);
    expandModalCharts(
        contID,
        expand_analysis_charts_rawdata,
        tempRes,
        '',
        undefined,
        alwaysFloatAxis('yaxis'),
        makeCaseKeyResolver(
            `${tempRes}-chart-raw-variable`,
            `${tempRes}-chart-raw-series`,
            `${tempRes}-chart-raw-plot-type`
        )
    );
    purgePlotlyChartExpandModal(contID);

    setAnalysisDateCalendarRaw(tempRes);
    setNamesCalendar(
        `${tempRes}-chart-raw-startmonth`,
        'monthly',
        $(`#${tempRes}-raw-control`),
        mapNavigation = false
    );

    if (tempRes === 'seasonal') {
        const variable = $(`#${tempRes}-chart-raw-variable`).val();
        const temp_cov = getTempCoverageCalendar(
            DATA_SET.use, tempRes, variable
        );
        const mon = -1 * SEASON_DEF.months.length + 1;
        const disp_d = addDateMonths(temp_cov.end, mon);
        const dispDate = formatDateToString(disp_d);
        const start_mon = parseInt(dispDate.split('-')[1], 10);

        setClimateSeasonStartLengthExpand(
            tempRes, 'chart-season', 'raw', start_mon
        );
    }

    //
    const contChart = `container-chart-${contID}`;

    const updateRawSeriesControls = () => {
        if ($(`#${tempRes}-chart-raw-series`).val() === 'one') {
            $(`#${tempRes}-chart-raw-startmonth-list`).hide();
            $(`#${tempRes}-chart-raw-plot-type-cont`).show();
        } else {
            $(`#${tempRes}-chart-raw-startmonth-list`).show();
            $(`#${tempRes}-chart-raw-plot-type-cont`).hide();
        }
    };
    updateRawSeriesControls();

    $(`#${tempRes}-chart-raw-series`)
        .off('change.chartTsRaw')
        .on('change.chartTsRaw', function() {
            updateRawSeriesControls();
            maproomDB.getData('ts_rawdata', function(data) {
                expand_analysis_display_rawdata(data, contChart);
            });
        });

    $(`#${tempRes}-chart-raw-variable`)
        .off('change.chartTsRaw')
        .on('change.chartTsRaw', function() {
            expand_analysis_charts_rawdata(contChart, tempRes);
        });

    $(`#${tempRes}-chart-raw-plot-type`)
        .off('change.chartTsRaw')
        .on('change.chartTsRaw', function() {
            maproomDB.getData('ts_rawdata', function(data) {
                expand_analysis_display_rawdata(data, contChart);
            });
        });

    $(`#${tempRes}-chart-raw-startmonth-calendar`)
        .off('change.chartTsRaw')
        .on('change.chartTsRaw', function() {
            maproomDB.getData('ts_rawdata', function(data) {
                expand_analysis_display_rawdata(data, contChart);
            });
        });

    if (tempRes === 'seasonal') {
        $(`#${tempRes}-chart-season-startmon`)
            .off('change.chartTsRaw')
            .on('change.chartTsRaw', function() {
                expand_analysis_charts_rawdata(contChart, tempRes);
            });

        $(`#${tempRes}-chart-season-seaslen`)
            .off('change.chartTsRaw')
            .on('change.chartTsRaw', function() {
                expand_analysis_charts_rawdata(contChart, tempRes);
            });
    }

    // update chart
    $(`#plotly-replot-${contID}`)
        .off('click.chartTsRaw')
        .on('click.chartTsRaw', function() {
            expand_analysis_charts_rawdata(contChart, tempRes);
        });

    // download chart
    $(`#plotly-download-${contID}`)
        .off('click.chartTsRaw')
        .on('click.chartTsRaw', function() {
            downloadPlotlyImageJPG(contChart);
        });
}

function setAnalysisExpandModalClim(tempRes, contID) {
    showModalDialog(`modal-expand-${contID}`);
    expandModalCharts(
        contID,
        expand_analysis_charts_climato,
        tempRes,
        '',
        undefined,
        combineAxisResolvers(alwaysFloatAxis('yaxis'), alwaysFloatAxis('yaxis2')),
        makeCaseKeyResolver(
            `${tempRes}-chart-clim-variable`,
            `${tempRes}-chart-clim-charts`
        ),
        ['year']
    );
    purgePlotlyChartExpandModal(contID);

    // 
    const contChart = `container-chart-${contID}`;

    const updateClimatoChartControls = () => {
        if ($(`#${tempRes}-chart-clim-charts`).val() === 'one') {
            $(`#${tempRes}-chart-clim-variable-cont`).show();
        } else {
            $(`#${tempRes}-chart-clim-variable-cont`).hide();
        }
    };
    updateClimatoChartControls();

    $(`#${tempRes}-chart-clim-charts`)
        .off('change.chartTsClim')
        .on('change.chartTsClim', function() {
            updateClimatoChartControls();
            expand_analysis_charts_climato(contChart, tempRes);
        });

    $(`#${tempRes}-chart-clim-variable`)
        .off('change.chartTsClim')
        .on('change.chartTsClim', function() {
            expand_analysis_charts_climato(contChart, tempRes);
        });

    // set base period
    setBoxDialog(
        `${tempRes}-chart-clim-bp`,
        `${tempRes}-chart-clim-bp-open`
    );

    // update chart
    $(`#plotly-replot-${contID}`)
        .off('click.chartTsClim')
        .on('click.chartTsClim', function() {
            expand_analysis_charts_climato(contChart, tempRes);
        });

    // download chart
    $(`#plotly-download-${contID}`)
        .off('click.chartTsClim')
        .on('click.chartTsClim', function() {
            downloadPlotlyImageJPG(contChart);
        });
}


const ANOM_DISALLOWED_TICK_UNITS = {
    monthly: ['day', 'week'],
    dekadal: ['day'],
    seasonal: ['day', 'week', 'month']
};

function setAnalysisExpandModalAnom(tempRes, contID) {
    showModalDialog(`modal-expand-${contID}`);
    expandModalCharts(
        contID,
        expand_analysis_charts_anomaly,
        tempRes,
        '',
        anomalySignColorsModule,
        alwaysFloatAxis('yaxis'),
        makeCaseKeyResolver(
            `${tempRes}-anom-variable`,
            `${tempRes}-chart-anom-type`
        ),
        ANOM_DISALLOWED_TICK_UNITS[tempRes] || []
    );
    purgePlotlyChartExpandModal(contID);

    let disp_year = false;
    if (tempRes === 'seasonal') {
        disp_year = true;
    }
    setAnalysisDateCalendarSeasonal(
        tempRes, 'chart-anom', 'anom', disp_year
    );
    setNamesCalendar(
        `${tempRes}-chart-anom-tstep`,
        tempRes,
        $(`#${tempRes}-anom-control`),
        mapNavigation = false
    );

    // 
    if (tempRes === 'seasonal') {
        setClimateSeasonLengthExpand(
            tempRes, 'chart-anom-seaslen'
        );
    }

    //
    const contChart = `container-chart-${contID}`;

    const updateAnomalySeriesControls = () => {
        if ($(`#${tempRes}-chart-anom-series`).val() === 'one') {
            $(`#${tempRes}-chart-anom-tstep-list`).hide();
        } else {
            $(`#${tempRes}-chart-anom-tstep-list`).show();
        }
    };
    updateAnomalySeriesControls();

    $(`#${tempRes}-chart-anom-series`)
        .off('change.chartTsAnom')
        .on('change.chartTsAnom', function() {
            updateAnomalySeriesControls();
            maproomDB.getData('ts_anomaly', function(data) {
                expand_analysis_display_anomaly(data, contChart);
            });
        });

    $(`#${tempRes}-anom-variable`)
        .off('change.chartTsAnom')
        .on('change.chartTsAnom', function() {
            expand_analysis_charts_anomaly(contChart, tempRes);
        });

    //
    $(`#${tempRes}-chart-anom-type`)
        .off('change.chartTsAnom')
        .on('change.chartTsAnom', function() {
            expand_analysis_charts_anomaly(contChart, tempRes);
        });

    $(`#${tempRes}-chart-anom-tstep-calendar`)
        .off('change.chartTsAnom')
        .on('change.chartTsAnom', function() {
            maproomDB.getData('ts_anomaly', function(data) {
                expand_analysis_display_anomaly(data, contChart);
            });
        });

    // 
    if (tempRes === 'seasonal') {
        $(`#${tempRes}-chart-anom-seaslen`)
            .off('change.chartTsAnom')
            .on('change.chartTsAnom', function() {
                expand_analysis_charts_anomaly(contChart, tempRes);
            });
    }

    // set base period
    setBoxDialog(
        `${tempRes}-chart-anom-bp`,
        `${tempRes}-chart-anom-bp-open`
    );

    // update chart
    $(`#plotly-replot-${contID}`)
        .off('click.chartTsAnom')
        .on('click.chartTsAnom', function() {
            expand_analysis_charts_anomaly(contChart, tempRes);
        });

    // download chart
    $(`#plotly-download-${contID}`)
        .off('click.chartTsAnom')
        .on('click.chartTsAnom', function() {
            downloadPlotlyImageJPG(contChart);
        });
}

function setAnalysisExpandModalDailyAnom(tempRes, contID) {
    showModalDialog(`modal-expand-${contID}`);
    expandModalCharts(
        contID,
        expand_analysis_charts_anomaly,
        tempRes,
        '',
        anomalySignColorsModule,
        alwaysFloatAxis('yaxis'),
        makeCaseKeyResolver(
            `${tempRes}-anom-variable`,
            `${tempRes}-anom-parameters`,
            `${tempRes}-chart-anom-type`
        )
    );
    purgePlotlyChartExpandModal(contID);

    setAnalysisDateCalendarSeasonal(
        tempRes, 'chart-anom', 'anom', true
    );
    setAnalysisDateCalendarMonDay(tempRes, 'anom');

    // 
    const contChart = `container-chart-${contID}`;

    $(`#${tempRes}-anom-variable`)
        .off('change.chartTsAnoma')
        .on('change.chartTsAnoma', function() {
            const this_var = $(this).val();
            $(`#${tempRes}-anom-parameters`).empty();
            for (const item of PARAMS_ORDER[this_var]) {
                $(`#${tempRes}-anom-parameters`).append(
                    $('<option>').val(item)
                    .text(PARAMS_LIST[this_var][item].select)
                );
                setAnalysisParamsDefDaily(tempRes, 'anom');
            }
            //
            expand_analysis_charts_anomaly(contChart, tempRes);
        });

    //
    $(`#${tempRes}-anom-parameters`)
        .off(`change.chartTsAnoma`)
        .on(`change.chartTsAnoma`, function() {
            setAnalysisParamsDefDaily(tempRes, 'anom');
            expand_analysis_charts_anomaly(contChart, tempRes);
        });

    $(`#${tempRes}-chart-anom-type`)
        .off('change.chartTsAnoma')
        .on('change.chartTsAnoma', function() {
            expand_analysis_charts_anomaly(contChart, tempRes);
        });

    // set base period
    setBoxDialog(
        `${tempRes}-chart-anom-bp`,
        `${tempRes}-chart-anom-bp-open`
    );

    // update chart
    $(`#plotly-replot-${contID}`)
        .off('click.chartTsAnom')
        .on('click.chartTsAnom', function() {
            expand_analysis_charts_anomaly(contChart, tempRes);
        });

    // download chart
    $(`#plotly-download-${contID}`)
        .off('click.chartTsAnom')
        .on('click.chartTsAnom', function() {
            downloadPlotlyImageJPG(contChart);
        });

    // setPlotlyChartSettingsDialog(contID, contChart, test_climate_analysis_season_daily);
}

function setProbaPlotContainer(data, container) {
    const divCont = $(`#${container}`);
    const divRow = $('<div>')
        .addClass('row flex-nowrap h-100')
        .appendTo(divCont);

    const cont_plot = `${container}-plot`;
    $('<div>')
        .attr('id', cont_plot)
        .addClass('col-md-8')
        .css({
            'width': '75%',
            'height': '100%'
        })
        .appendTo(divRow);

    const div_distr = `${container}-distr-div`;
    const divDistr = $('<div>')
        .attr('id', div_distr)
        .addClass('col-md-4 m-2 p-2')
        .css({
            'width': '22%',
            'height': '84%',
            'border': '1px solid #d0d7de'
        })
        .appendTo(divRow);

    $('<h5>')
        .appendTo(divDistr)
        .text('Fitted Distribution');

    const frmtJson = JSON.stringify(
        data.info.proba, null, 2
    );
    const pre_distr = `${container}-distr-pre`;
    $('<pre>')
        .attr('id', pre_distr)
        .appendTo(divDistr)
        .text(frmtJson);

    divDistr.hide();

    return cont_plot
}

function setAnalysisExpandModalProba(tempRes, contID) {
    showModalDialog(`modal-expand-${contID}`);
    const probaCaseKeySelectors = [`${tempRes}-proba-variable`];
    if (tempRes === 'daily') {
        probaCaseKeySelectors.push(`${tempRes}-proba-parameters`);
    }
    probaCaseKeySelectors.push(`${tempRes}-chart-proba-plot-type`);
    expandModalCharts(
        contID,
        expand_analysis_charts_proba,
        tempRes,
        '-plot',
        undefined,
        combineAxisResolvers(
            alwaysFloatAxis('yaxis'),
            parameterDrivenAxis(
                'xaxis',
                `${tempRes}-proba-variable`,
                tempRes === 'daily' ? `${tempRes}-proba-parameters` : null
            )
        ),
        makeCaseKeyResolver(...probaCaseKeySelectors)
    );
    purgePlotlyChartExpandModal(contID);

    setAnalysisDateCalendarSeasonal(
        tempRes, 'chart-proba', 'proba', true
    );
    if (tempRes === 'daily') {
        setAnalysisDateCalendarMonDay(tempRes, 'proba');
    }
    if (tempRes === 'seasonal') {
        setClimateSeasonStartLengthExpand(
            tempRes, 'chart-proba', 'proba'
        );
    }

    //
    const contChart = `container-chart-${contID}`;

    $(`#${tempRes}-proba-variable`)
        .off('change.chartTsProba')
        .on('change.chartTsProba', function() {
            if (tempRes === 'daily') {
                const this_var = $(this).val();
                $(`#${tempRes}-proba-parameters`).empty();
                for (const item of PARAMS_ORDER[this_var]) {
                    $(`#${tempRes}-proba-parameters`).append(
                        $('<option>').val(item)
                        .text(PARAMS_LIST[this_var][item].select)
                    );
                }
                setAnalysisParamsDefDaily(tempRes, 'proba');
            }
            //
            expand_analysis_charts_proba(contChart, tempRes);
        });

    //
    if (tempRes === 'daily') {
        $(`#${tempRes}-proba-parameters`)
            .off(`change.chartTsProba`)
            .on(`change.chartTsProba`, function() {
                setAnalysisParamsDefDaily(tempRes, 'proba');
                expand_analysis_charts_proba(contChart, tempRes);
            });
    }

    // 
    if (tempRes === 'seasonal') {
        const sDId = `${tempRes}-chart-proba`;
        $(`#${sDId}-seaslen, #${sDId}-startmon-calendar`)
            .off('change.chartTsProba')
            .on('change.chartTsProba', function() {
                expand_analysis_charts_proba(contChart, tempRes);
            });
    }
    // 

    const updateProbaDataControls = () => {
        if ($(`#${tempRes}-chart-proba-plot-type`).val() === 'cdf') {
            $(`#${tempRes}-chart-proba-plot-cdf`).show();
            $(`#${tempRes}-chart-proba-plot-pdf`).hide();
        } else {
            $(`#${tempRes}-chart-proba-plot-cdf`).hide();
            $(`#${tempRes}-chart-proba-plot-pdf`).show();
        }
    };
    updateProbaDataControls();

    $(`#${tempRes}-chart-proba-plot-type`)
        .off('change.chartTsProba')
        .on('change.chartTsProba', function() {
            updateProbaDataControls();
            maproomDB.getData('data_proba', function(data) {
                expand_analysis_display_proba(data, contChart);
            });
        });

    $(`.${tempRes}-proba-plot`)
        .off('change.chartTsProba')
        .on('change.chartTsProba', function() {
            const pKind = $(this).data('plot');
            const pType = $(this).val();
            const isVisible = $(this).is(':checked');

            const ix = PROBA_PLOT[pKind].indexOf(pType);

            Plotly.restyle(`${contChart}-plot`, {
                visible: isVisible
            }, [ix]);

            if (pType === 'fitted') {
                $(`#${contChart}-distr-div`).toggle(isVisible);
            }
        });

    // update chart
    $(`#plotly-replot-${contID}`)
        .off('click.chartTsProba')
        .on('click.chartTsProba', function() {
            expand_analysis_charts_proba(contChart, tempRes);
        });

    // download chart
    $(`#plotly-download-${contID}`)
        .off('click.chartTsProba')
        .on('click.chartTsProba', function() {
            downloadPlotlyImageJPG(`${contChart}-plot`);
        });

    // setPlotlyChartSettingsDialog(contID, contChart, test_climate_analysis_season_daily);
}

function setAnalysisExpandModalSeason(tempRes, contID) {
    showModalDialog(`modal-expand-${contID}`);
    const seasonCaseKeySelectors = [`${tempRes}-tseries-variable`];
    if (tempRes === 'daily') {
        seasonCaseKeySelectors.push(`${tempRes}-tseries-parameters`);
    }
    seasonCaseKeySelectors.push(`${tempRes}-chart-season-plot-type`);
    expandModalCharts(
        contID,
        expand_analysis_charts_season,
        tempRes,
        '',
        undefined,
        combineAxisResolvers(
            yearIndexAxis('xaxis'),
            parameterDrivenAxis(
                'yaxis',
                `${tempRes}-tseries-variable`,
                tempRes === 'daily' ? `${tempRes}-tseries-parameters` : null
            )
        ),
        makeCaseKeyResolver(...seasonCaseKeySelectors)
    );
    purgePlotlyChartExpandModal(contID);

    setAnalysisDateCalendarSeasonal(
        tempRes, 'chart-season', 'tseries', true
    );
    if (tempRes === 'daily') {
        setAnalysisDateCalendarMonDay(tempRes, 'tseries');
    }
    if (tempRes === 'seasonal') {
        setClimateSeasonStartLengthExpand(
            tempRes, 'chart-season', 'season'
        );
    }

    //
    const contChart = `container-chart-${contID}`;

    $(`#${tempRes}-tseries-variable`)
        .off('change.chartTsSeason')
        .on('change.chartTsSeason', function() {
            if (tempRes === 'daily') {
                const this_var = $(this).val();
                $(`#${tempRes}-tseries-parameters`).empty();
                for (const item of PARAMS_ORDER[this_var]) {
                    $(`#${tempRes}-tseries-parameters`).append(
                        $('<option>').val(item)
                        .text(PARAMS_LIST[this_var][item].select)
                    );
                }
                setAnalysisParamsDefDaily(tempRes, 'tseries');
            }
            //
            expand_analysis_charts_season(contChart, tempRes);
        });

    //
    if (tempRes === 'daily') {
        $(`#${tempRes}-tseries-parameters`)
            .off(`change.chartTsSeason`)
            .on(`change.chartTsSeason`, function() {
                setAnalysisParamsDefDaily(tempRes, 'tseries');
                expand_analysis_charts_season(contChart, tempRes);
            });
    }

    // 
    if (tempRes === 'seasonal') {
        const sDId = `${tempRes}-chart-season`;
        $(`#${sDId}-seaslen, #${sDId}-startmon-calendar`)
            .off('change.chartTsSeason')
            .on('change.chartTsSeason', function() {
                expand_analysis_charts_season(contChart, tempRes);
            });
    }

    // update chart
    $(`#plotly-replot-${contID}`)
        .off('click.chartTsSeason')
        .on('click.chartTsSeason', function() {
            expand_analysis_charts_season(contChart, tempRes);
        });

    // download chart
    $(`#plotly-download-${contID}`)
        .off('click.chartTsSeason')
        .on('click.chartTsSeason', function() {
            downloadPlotlyImageJPG(contChart);
        });
}

function setAnalysisExpandModalEnso(tempRes, contID) {
    showModalDialog(`modal-expand-${contID}`);
    expandModalCharts(
        contID,
        expand_analysis_charts_enso,
        tempRes,
        '',
        undefined,
        alwaysFloatAxis('yaxis'),
        makeCaseKeyResolver(
            `${tempRes}-enso-indices`,
            `${tempRes}-anom-tempres`,
            `${tempRes}-anom-sstweek`,
            `${tempRes}-anom-sstmonth`,
            `${tempRes}-oni-indices`,
            `${tempRes}-iod-sst`,
            `${tempRes}-anom-ninotype`,
            `${tempRes}-anom-ninoregion`,
            `${tempRes}-disp-image-enso`
        )
    );

    const contChart = `container-chart-${contID}`;

    $(`#${tempRes}-enso-indices`)
        .off('change.teleconIndex')
        .on('change.teleconIndex', function() {
            setAnalysisDateCalendarEnso(tempRes);
            setAnalysisVisibilityEnso(tempRes);
            expand_analysis_charts_enso(contChart, tempRes);
        });

    $(`#${tempRes}-anom-tempres`)
        .off('change.teleconIndex')
        .on('change.teleconIndex', function() {
            setAnalysisDateCalendarEnso(tempRes);
            setAnalysisVisibilityEnso(tempRes);
            setAnalysisAnomaliesEnso(contChart, tempRes);
            expand_analysis_charts_enso(contChart, tempRes);
        });

    $(`#${tempRes}-anom-sstweek`)
        .off('change.teleconIndex')
        .on('change.teleconIndex', function() {
            setAnalysisDateCalendarEnso(tempRes);
            setAnalysisAnomaliesEnso(contChart, tempRes);
            expand_analysis_charts_enso(contChart, tempRes);
        });

    $(`#${tempRes}-anom-sstmonth`)
        .off('change.teleconIndex')
        .on('change.teleconIndex', function() {
            setAnalysisDateCalendarEnso(tempRes);
            setAnalysisAnomaliesEnso(contChart, tempRes);
            expand_analysis_charts_enso(contChart, tempRes);
        });

    // 
    $(`#${tempRes}-oni-indices`)
        .off('change.teleconIndex')
        .on('change.teleconIndex', function() {
            expand_analysis_charts_enso(contChart, tempRes);
        });

    $(`#${tempRes}-iod-sst`)
        .off('change.teleconIndex')
        .on('change.teleconIndex', function() {
            expand_analysis_charts_enso(contChart, tempRes);
        });

    $(`#${tempRes}-anom-ninotype`)
        .off('change.teleconIndex')
        .on('change.teleconIndex', function() {
            expand_analysis_charts_enso(contChart, tempRes);
        });

    $(`#${tempRes}-anom-ninoregion`)
        .off('change.teleconIndex')
        .on('change.teleconIndex', function() {
            expand_analysis_charts_enso(contChart, tempRes);
        });

    $(`#${tempRes}-disp-image-enso`)
        .off('change.teleconIndex')
        .on('change.teleconIndex', function() {
            const this_image = $(this).val();
            if (this_image === 'image') {
                $(`#${tempRes}-disp-lastval-enso-opt`).show();
            } else {
                $(`#${tempRes}-disp-lastval-enso-opt`).hide();
            }
            expand_analysis_charts_enso(contChart, tempRes);
        });

    $(`#${tempRes}-disp-lastval-enso`)
        .off('change.teleconIndex')
        .on('change.teleconIndex', function() {
            expand_analysis_charts_enso(contChart, tempRes);
        });

    // update chart
    $(`#plotly-replot-${contID}`)
        .off('click.teleconIndex')
        .on('click.teleconIndex', function() {
            const ensoIdx = $(`#${tempRes}-enso-indices`).val();
            if (['oni', 'anom', 'iod', 'nao', 'atl3'].includes(ensoIdx)) {
                expand_analysis_charts_enso(contChart, tempRes);
            }
        });

    // download chart
    $(`#plotly-download-${contID}`)
        .off('click.teleconIndex')
        .on('click.teleconIndex', function() {
            const ensoIdx = $(`#${tempRes}-enso-indices`).val();
            if (['proba', 'strength'].includes(ensoIdx)) {
                downloadImageSrcPNG(contChart);
            } else {
                const ensoImg = $(`#${tempRes}-disp-image-enso`).val();
                if (ensoImg === 'image') {
                    downloadImageSrcPNG(contChart);
                } else {
                    downloadPlotlyImageJPG(contChart);
                }
            }

        });
}

function setAnalysisExpandModalTelecon(tempRes, contID, cType) {
    const expandFunction = {
        'tseries': expand_analysis_telecon_tseries,
        'proba': expand_analysis_telecon_proba
    };
    const axisKindResolvers = {
        tseries: combineAxisResolvers(yearIndexAxis('xaxis'), alwaysFloatAxis('yaxis')),
        proba: combineAxisResolvers(alwaysFloatAxis('xaxis'), alwaysFloatAxis('yaxis'))
    };
    const colorsModules = {
        tseries: telecomTercileBarColorsModule,
        proba: undefined
    };

    showModalDialog(`modal-expand-${contID}`);
    expandModalCharts(
        contID,
        expandFunction[cType],
        tempRes,
        '',
        colorsModules[cType],
        axisKindResolvers[cType],
        makeCaseKeyResolver(
            `${tempRes}-${cType}-variable`,
            `${tempRes}-${cType}-clim-variable`,
            `${tempRes}-${cType}-index-telecon`
        )
    );
    purgePlotlyChartExpandModal(contID);

    // const this_var = $(`#${tempRes}-${cType}-variable`).val();
    setAnalysisDateCalendarSeasonal(
        tempRes, cType, cType, true
    );
    setClimateSeasonStartLengthExpand(
        tempRes, cType, `${cType}-telecon`
    );

    const contChart = `container-chart-${contID}`;

    $(`#${tempRes}-${cType}-variable`)
        .off(`change.${cType}Telecon`)
        .on(`change.${cType}Telecon`, function() {
            setClimateVariableTelecon(
                tempRes, $(this).val(), `${cType}-clim-variable`
            );
            setAnalysisDateCalendarSeasonal(
                tempRes, cType, cType, true
            );
            expandFunction[cType](contChart, tempRes);
        });

    $(`#${tempRes}-${cType}-clim-variable`)
        .off(`change.${cType}Telecon`)
        .on(`change.${cType}Telecon`, function() {
            expandFunction[cType](contChart, tempRes);
        });

    $(`#${tempRes}-${cType}-index-telecon`)
        .off(`change.${cType}Telecon`)
        .on(`change.${cType}Telecon`, function() {
            expandFunction[cType](contChart, tempRes);
        });

    // update chart
    $(`#plotly-replot-${contID}`)
        .off(`click.${cType}Telecon`)
        .on(`click.${cType}Telecon`, function() {
            expandFunction[cType](contChart, tempRes);
        });

    // download chart
    $(`#plotly-download-${contID}`)
        .off(`click.${cType}Telecon`)
        .on(`click.${cType}Telecon`, function() {
            downloadPlotlyImageJPG(contChart);
        });
}

function setRainySeasonExpandModal(tempRes, chartType, contID) {
    const expandFunction = {
        'series': expand_agri_rseason_charts_series,
        'proba': expand_agri_rseason_charts_proba,
        'anom': expand_agri_rseason_charts_anom
    };
    // the anomaly view colors each bar by sign (positive/negative), same
    // as the general Anomaly chart - needs the sign-aware colors module,
    // not the default one-color-per-trace picker
    const colorsModule = {
        'anom': anomalySignColorsModule
    };

    showModalDialog(`modal-expand-${contID}`);
    const prefixID = `${tempRes}-${chartType}`;
    const caseKeySelectors = [`${prefixID}-variable`];
    if (chartType === 'series') {
        caseKeySelectors.push(`${prefixID}-plot-type`);
    }
    const axisKindResolver = ['series', 'anom'].includes(chartType) ? yearIndexAxis('xaxis') : null;
    expandModalCharts(
        contID,
        expandFunction[chartType],
        tempRes,
        '',
        colorsModule[chartType],
        axisKindResolver,
        makeCaseKeyResolver(...caseKeySelectors)
    );
    purgePlotlyChartExpandModal(contID);

    const contChart = `container-chart-${contID}`;


    setBoxDialog(
        `${prefixID}-rseason-def`,
        `${prefixID}-rseason-def-open`
    );
    setRainySeasonCalendarOnset(tempRes, chartType);

    $(`#${prefixID}-variable`)
        .off('change.chartRSeason')
        .on('change.chartRSeason', function() {
            expandFunction[chartType](contChart, tempRes);
        });

    $(`.${tempRes}-proba-plot`)
        .off('change.chartRSeason')
        .on('change.chartRSeason', function() {
            const pType = $(this).val();
            const ix = ['empirical', 'smoothed'].indexOf(pType);

            Plotly.restyle(contChart, {
                visible: $(this).is(':checked')
            }, [ix]);
        });

    // update chart
    $(`#plotly-replot-${contID}`)
        .off('click.chartRSeason')
        .on('click.chartRSeason', function() {
            expandFunction[chartType](contChart, tempRes);
        });

    // download chart
    $(`#plotly-download-${contID}`)
        .off('click.chartRSeason')
        .on('click.chartRSeason', function() {
            downloadPlotlyImageJPG(contChart);
        });
}

function setCropSuitabilityExpandModal(tempRes, contID) {
    showModalDialog(`modal-expand-${contID}`);
    // bars are colored from a fixed 6-step suitability-score palette
    // (0-5) plus a "no data" gray, not one color per trace - needs the
    // categorical colors module
    expandModalCharts(
        contID,
        expand_agri_cropsuit_charts,
        tempRes,
        '',
        categoricalMarkerColorsModule,
        yearIndexAxis('xaxis')
    );
    purgePlotlyChartExpandModal(contID);

    setAnalysisDateCalendarMonDay(tempRes, 'cs-ts');

    const contChart = `container-chart-${contID}`;

    $(`#plotly-replot-${contID}`)
        .off('click.chartCropSuit')
        .on('click.chartCropSuit', function() {
            expand_agri_cropsuit_charts(contChart, tempRes);
        });

    $(`#plotly-download-${contID}`)
        .off('click.chartCropSuit')
        .on('click.chartCropSuit', function() {
            downloadPlotlyImageJPG(contChart);
        });
}

function setAnalysisExpandModalCumul(tempRes, contID) {
    showModalDialog(`modal-expand-${contID}`);
    expandModalCharts(
        contID,
        expand_analysis_charts_cumul,
        tempRes
    );
    purgePlotlyChartExpandModal(contID);

    // set base period
    setBoxDialog(
        `${tempRes}-chart-cumul-bp`,
        `${tempRes}-chart-cumul-bp-open`
    );

    const end_date = $(`#${tempRes}-chart-cumul-enddate-calendar`).val();
    let disp_end;
    if (end_date === '') {
        disp_end = null;
    } else {
        if (end_date.length == 4) {
            disp_end = `${end_date}-12`;
        } else {
            disp_end = end_date;
        }
    }

    setDateCalendar(
        `${tempRes}-chart-cumul-enddate`,
        `${tempRes}-chart-cumul-variable`,
        DATA_SET.use,
        tempRes, disp_end,
        mapNavigation = false,
        isStart = false
    );

    const variable = $(`#${tempRes}-chart-cumul-variable`).val();
    const start_date = $(`#${tempRes}-chart-cumul-startdate-calendar`).val();
    let disp_start;
    if (start_date === '') {
        disp_start = getStartDekadCumul(tempRes, variable);
    } else {
        if (start_date.length == 4) {
            disp_start = `${start_date}-01`;
        } else {
            disp_start = start_date;
        }
    }

    setDateCalendar(
        `${tempRes}-chart-cumul-startdate`,
        `${tempRes}-chart-cumul-variable`,
        DATA_SET.use,
        tempRes,
        dispDate = disp_start,
        mapNavigation = true,
        dispYear = false,
        isStart = null,
        ensoData = false
    );

    const contChart = `container-chart-${contID}`;

    // update chart
    $(`#plotly-replot-${contID}`)
        .off('click.chartCumul')
        .on('click.chartCumul', function() {
            expand_analysis_charts_cumul(contChart, tempRes);
        });

    // download chart
    $(`#plotly-download-${contID}`)
        .off('click.chartCumul')
        .on('click.chartCumul', function() {
            downloadPlotlyImageJPG(contChart);
        });
}

function setAnalysisExpandModalSPEI(tempRes, contID) {
    showModalDialog(`modal-expand-${contID}`);
    expandModalCharts(
        contID,
        expand_analysis_charts_spei_ts,
        tempRes
    );
    purgePlotlyChartExpandModal(contID);

    const disp_year = tempRes === 'seasonal';
    setAnalysisDateCalendarSeasonal(
        tempRes, 'chart-spei', 'spei', disp_year
    );

    setAnalysisTimeScaleSPEI(
        tempRes, 'chart-spei-timescale', 12
    );

    //
    const contChart = `container-chart-${contID}`;

    $(`#${tempRes}-chart-spei-analysis`)
        .off('change.chartTsSpei')
        .on('change.chartTsSpei', function() {
            setAnalysisDistributionSPEI(tempRes, $(this).val());
            setTimeout(() => {
                expand_analysis_charts_spei_ts(contChart, tempRes);
            }, 30);
        });

    $(`#${tempRes}-chart-spei-distr`)
        .off('change.chartTsSpei')
        .on('change.chartTsSpei', function() {
            expand_analysis_charts_spei_ts(contChart, tempRes);
        });

    // update chart
    $(`#plotly-replot-${contID}`)
        .off('click.chartTsSpei')
        .on('click.chartTsSpei', function() {
            expand_analysis_charts_spei_ts(contChart, tempRes);
        });

    // download chart
    $(`#plotly-download-${contID}`)
        .off('click.chartTsSpei')
        .on('click.chartTsSpei', function() {
            downloadPlotlyImageJPG(contChart);
        });
}

function setAnalysisDistributionSPEI(tempRes, analysis) {
    let distr_obj = makeCopy(OPT_SPEI.distr_function);
    if (analysis === 'spei') {
        distr_obj = { llogistic: distr_obj.llogistic };
    }

    const speiDistr = $(`#${tempRes}-chart-spei-distr`);
    speiDistr.empty();
    for (const [k, v] of Object.entries(distr_obj)) {
        speiDistr.append(
            $('<option>').text(v).val(k)
        );
    }
}

function setAnalysisExpandModalDrmExt_cdf(tempRes, contID) {
    showModalDialog(`modal-expand-${contID}`);
    expandModalCharts(
        contID,
        expand_analysis_charts_drmExt_cdf,
        tempRes
    );
    purgePlotlyChartExpandModal(contID);
    //
    setAnalysisDateCalendarSeasonal(
        tempRes, 'chart-proba', 'map', true
    );

    setAnalysisDateCalendarMonDay(tempRes, 'proba');

    const contChart = `container-chart-${contID}`;
    $(`#plotly-replot-${contID}`)
        .off('click.drmExtReplot')
        .on('click.drmExtReplot', () => {
            expand_analysis_charts_drmExt_cdf(
                contChart,
                tempRes
            );
        });

    $(`#${tempRes}-proba-parameters`)
        .off('change.drmExtExpandParameters')
        .on('change.drmExtExpandParameters', function() {
            const this_val = $(this).val();

            if (['TotRain', 'seasAvg'].includes(this_val)) {
                setVisibility(
                    [],
                    [
                        `${tempRes}-proba-def-number`,
                        `${tempRes}-proba-def-spell`
                    ]
                );
            } else if (
                ['NumWD', 'NumDD', 'RainInt', 'NumCD', 'NumHD'].includes(this_val)
            ) {
                setVisibility(
                    [
                        `${tempRes}-proba-def-number`
                    ],
                    [
                        `${tempRes}-proba-def-spell`
                    ]
                );
            } else {
                setVisibility(
                    [
                        `${tempRes}-proba-def-number`,
                        `${tempRes}-proba-def-spell`
                    ],
                    []
                );
            }

            expand_analysis_charts_drmExt_cdf(contChart, tempRes);
        });

    $(`#${tempRes}-proba-parameters`).trigger('change');


}

function setAnalysisExpandModalDrmExt_pdf(tempRes, contID) {
    showModalDialog(`modal-expand-${contID}`);
    expandModalCharts(
        contID,
        expand_analysis_charts_drmExt_pdf,
        tempRes
    );
    purgePlotlyChartExpandModal(contID);
    //
    setAnalysisDateCalendarSeasonal(
        tempRes, 'chart-pdf', 'map', true
    );

    setAnalysisDateCalendarMonDay(tempRes, 'pdf');

    const contChart = `container-chart-${contID}`;
    $(`#plotly-replot-${contID}`)
        .off('click.drmExtReplot')
        .on('click.drmExtReplot', () => {
            expand_analysis_charts_drmExt_pdf(
                contChart,
                tempRes
            );
        });

    $(`#${tempRes}-pdf-parameters`)
        .off('change.drmExtExpandParameters')
        .on('change.drmExtExpandParameters', function() {
            const this_val = $(this).val();

            if (['TotRain', 'seasAvg'].includes(this_val)) {
                setVisibility(
                    [],
                    [
                        `${tempRes}-pdf-def-number`,
                        `${tempRes}-pdf-def-spell`
                    ]
                );
            } else if (
                ['NumWD', 'NumDD', 'RainInt', 'NumCD', 'NumHD'].includes(this_val)
            ) {
                setVisibility(
                    [
                        `${tempRes}-pdf-def-number`
                    ],
                    [
                        `${tempRes}-pdf-def-spell`
                    ]
                );
            } else {
                setVisibility(
                    [
                        `${tempRes}-pdf-def-number`,
                        `${tempRes}-pdf-def-spell`
                    ],
                    []
                );
            }

            expand_analysis_charts_drmExt_pdf(contChart, tempRes);
        });

    $(`#${tempRes}-pdf-parameters`).trigger('change');

}


//////

function setProjectionExpandModalDistribution(tempRes, contID) {
    showModalDialog(`modal-expand-${contID}`);

    expandModalCharts(
        contID,
        expand_projection_charts_distribution,
        tempRes
    );

    purgePlotlyChartExpandModal(contID);

    const prefix = `${tempRes}-distribution-proj`;
    const source = `${tempRes}-seasonal-proj`;
    const contChart = `container-chart-${contID}`;

    setOffCanvasMapControlSeasonalProjection(tempRes, prefix);


    const fields = [
        'variable',
        'gcm',
        'scenario',
        'start-month',
        'end-month',
        'future-date-calendar',
        'period-length'
    ];

    fields.forEach(field => {
        $(`#${prefix}-${field}`)
            .val($(`#${source}-${field}`).val())
            .trigger('change.select2');
    });

    $(`.${prefix}-select2`).each(function() {
        const select = $(this);

        if (!select.hasClass('select2-hidden-accessible')) {
            select.select2({
                minimumResultsForSearch: -1,
                dropdownParent: $(`#${prefix}-control`)
            });
        }
    });

    const selectors = fields
        .map(field => `#${prefix}-${field}`)
        .join(', ');

    $(selectors)
        .off('change.chartProjectionDistribution')
        .on('change.chartProjectionDistribution', function() {
            expand_projection_charts_distribution(
                contChart,
                tempRes
            );
        });


    $(`#${prefix}-plot-type`)
        .off('change.chartProjectionDistribution')
        .on('change.chartProjectionDistribution', function() {
            maproomDB.getData(
                'projection_distribution',
                function(data) {
                    if (!data) {
                        expand_projection_charts_distribution(
                            contChart,
                            tempRes
                        );
                        return;
                    }

                    expand_projection_display_distribution(
                        data,
                        contChart
                    );
                }
            );
        });


    $(`#plotly-replot-${contID}`)
        .off('click.chartProjectionDistribution')
        .on('click.chartProjectionDistribution', function() {
            expand_projection_charts_distribution(
                contChart,
                tempRes
            );
        });

    $(`#plotly-download-${contID}`)
        .off('click.chartProjectionDistribution')
        .on('click.chartProjectionDistribution', function() {
            downloadPlotlyImageJPG(contChart);
        });
}



function setProjectionExpandModalSeries(tempRes, contID) {
    const prefix = `${tempRes}-series-proj`;
    const source = `${tempRes}-seasonal-proj`;
    const contChart = `container-chart-${contID}`;

    setOffCanvasMapControlSeasonalProjection(tempRes, prefix);

    const fields = [
        'variable',
        'start-month',
        'end-month'
    ];

    fields.forEach(field => {
        $(`#${prefix}-${field}`)
            .val($(`#${source}-${field}`).val())
            .trigger('change.select2');
    });

    const scenarioSelect = $(`#${prefix}-scenarios`);
    const previousScenarios = scenarioSelect.val();

    scenarioSelect.val(
        previousScenarios && previousScenarios.length
            ? previousScenarios
            : ['ssp1_2_6', 'ssp5_8_5']
    ).trigger('change.select2');

    $(`.${prefix}-select2`).each(function() {
        const select = $(this);

        if (!select.hasClass('select2-hidden-accessible')) {
            select.select2({
                minimumResultsForSearch: -1,
                closeOnSelect: !select.prop('multiple'),
                dropdownParent: $(`#${prefix}-control`)
            });
        }
    });

    const redraw = () => {
        expand_projection_charts_series(contChart, tempRes);
    };

    const selectors = fields
        .map(field => `#${prefix}-${field}`)
        .join(', ');

    $(selectors)
        .off('change.chartProjectionSeries')
        .on('change.chartProjectionSeries', redraw);

    // Recalculate after the user finishes selecting scenarios.
    scenarioSelect
        .off('select2:close.chartProjectionSeries')
        .on('select2:close.chartProjectionSeries', redraw);

    $(`#${prefix}-plot-type`)
        .off('change.chartProjectionSeries')
        .on('change.chartProjectionSeries', function() {
            maproomDB.getData(
                'projection_series_expand',
                function(data) {
                    if (!data) {
                        redraw();
                        return;
                    }

                    expand_projection_display_series(
                        data,
                        contChart
                    );
                }
            );
        });

    $(`#plotly-replot-${contID}`)
        .off('click.chartProjectionSeries')
        .on('click.chartProjectionSeries', redraw);

    $(`#plotly-download-${contID}`)
        .off('click.chartProjectionSeries')
        .on('click.chartProjectionSeries', function() {
            downloadPlotlyImageJPG(contChart);
        });

    showModalDialog(`modal-expand-${contID}`);

    expandModalCharts(
        contID,
        expand_projection_charts_series,
        tempRes
    );

    purgePlotlyChartExpandModal(contID);
}

/////
async function setProjectionExpandModalSpi(tempRes, contID) {
    const prefix = `${tempRes}-chart-spi-proj`;
    const source = `${tempRes}-spi-proj`;
    const container = `container-chart-${contID}`;

    showModalDialog(`modal-expand-${contID}`);

    ['gcm', 'scenario', 'distribution'].forEach(field => {
        $(`#${prefix}-${field}`)
            .val($(`#${source}-${field}`).val())
            .trigger('change.select2');
    });

    setProjectionSpiControls(prefix, source);

    $(`.${prefix}-select2`).each(function() {
        const select = $(this);

        if (!select.hasClass('select2-hidden-accessible')) {
            select.select2({
                minimumResultsForSearch: -1,
                dropdownParent: $(`#${prefix}-control`)
            });
        }
    });

    const ready = await setProjectionSpiDateCalendars(
        tempRes,
        prefix
    );

    if (!ready) {
        return;
    }

    const draw = () => {
        expand_projection_spi_charts(container, tempRes);
    };

    expandModalCharts(
        contID,
        expand_projection_spi_charts,
        tempRes
    );

    purgePlotlyChartExpandModal(contID);
    $(`#rangeselector-${contID}`).show();

    $(`#${prefix}-gcm, #${prefix}-scenario, #${prefix}-timescale`)
        .off('change.projectionSpiExpand')
        .on('change.projectionSpiExpand', async function() {
            if (await setProjectionSpiDateCalendars(
                tempRes,
                prefix
            )) {
                draw();
            }
        });

    $(`#${prefix}-distribution, #${prefix}-plot-start, #${prefix}-plot-end`)
        .off('change.projectionSpiExpand')
        .on('change.projectionSpiExpand', draw);

    $(`#plotly-replot-${contID}`)
        .off('click.projectionSpiExpand')
        .on('click.projectionSpiExpand', draw);

    $(`#plotly-download-${contID}`)
        .off('click.projectionSpiExpand')
        .on('click.projectionSpiExpand', () => {
            downloadPlotlyImageJPG(container);
        });
}


///////

async function setHealthWaspExpandedControls(tempRes) {
    const prefix = `${tempRes}-wasp-chart`;
    const parent = $(`#${tempRes}-health-wasp-control`);
    const area = $(`#${prefix}-area`);
    const month = $(`#${prefix}-comparison-month`);

    if (!area.data('waspAreasReady')) {
        let subdivisions = SUBDIV_BE;

        if (!subdivisions) {
            const json = await $.getJSON(
                '/map_subdivisions_data'
            );

            if (json.status !== 0) {
                throw new Error(
                    json.message ||
                    'Unable to load administrative areas.'
                );
            }

            subdivisions = json.data;
        }

        const options = [{
            id: 'country',
            text: area.attr('data-country-label')
        }];

        ['region', 'zone'].forEach(key => {
            const layer = LAYERS.subdivision[key];
            const source = subdivisions[key];

            if (!layer || !source) {
                return;
            }

            const geojson = typeof source === 'string'
                ? JSON.parse(source)
                : source;

            const names = [...new Set(
                geojson.features
                    .map(feature => feature.properties.field)
                    .filter(name =>
                        name !== null && name !== undefined
                    )
                    .map(String)
            )].sort((a, b) => a.localeCompare(b));

            options.push({
                text: typeof layer.name === 'string'
                    ? layer.name
                    : key,
                children: names.map(name => ({
                    id: JSON.stringify([key, name]),
                    text: name
                }))
            });
        });

        area.empty().select2({
            data: options,
            dropdownParent: parent,
            minimumResultsForSearch: 0
        });

        area.val('country').trigger('change.select2');
        area.data('waspAreasReady', true);
    }

    // if (month.children('option').length === 0) {
    //     getListOfMonthsCalendar().short.forEach(
    //         (label, index) => {
    //             month.append(
    //                 new Option(label, index + 1)
    //             );
    //         }
    //     );

    //     month.val(
    //         String(month.attr('data-default') || 1)
    //     );
    // }

    // if (!month.hasClass('select2-hidden-accessible')) {
    //     month.select2({
    //         dropdownParent: parent,
    //         minimumResultsForSearch: -1
    //     });
    // }


    const monthHolder = `${prefix}-comparison-month`;

    if (!$(`#${monthHolder}-calendar`).length) {
        setNamesCalendar(
            monthHolder,
            'monthly',
            parent,
            false,
            Number(
                $(`#${monthHolder}`).attr('data-default') || 1
            )
        );
    }

    const coverage = $(`#${prefix}-control`)
        .data('waspCoverage');

    ['comparison-start', 'comparison-end'].forEach(field => {
        const input = $(`#${prefix}-${field}`);
        const value = Number(input.val());

        input.attr({
            min: coverage.plot_start_year,
            max: coverage.plot_end_year
        });

        input.val(Math.max(
            coverage.plot_start_year,
            Math.min(
                Number.isInteger(value)
                    ? value
                    : coverage.plot_start_year,
                coverage.plot_end_year
            )
        ));
    });

    const start = $(`#${prefix}-comparison-start`);
    const end = $(`#${prefix}-comparison-end`);

    if (Number(start.val()) > Number(end.val())) {
        end.val(start.val());
    }
}


async function setHealthExpandModalWasp(tempRes, contID) {
    const source = `${tempRes}-wasp-map`;
    const prefix = `${tempRes}-wasp-chart`;
    const container = `container-chart-${contID}`;
    const modal = $(`#modal-expand-${contID}`);
    const controls = $(`#${tempRes}-health-wasp-control`);

    const query = queryParamsHealthWasp(tempRes, source);

    if (!query) {
        return false;
    }

    controls.data('waspBusy', true);
    controls.off('.healthWaspExpanded');
    controls.off('.healthWaspCalculation');

    [
        'timescale',
        'base-start',
        'base-end',
        'base-min'
    ].forEach(field => {
        $(`#${prefix}-${field}`)
            .val($(`#${source}-${field}`).val())
            .trigger('change.select2');
    });

    setHealthWaspControls(prefix);
    showModalDialog(`modal-expand-${contID}`);

    try {
        const ready = await setHealthWaspDateCalendars(
            tempRes,
            prefix
        );

        if (!ready) {
            return false;
        }

        await setHealthWaspExpandedControls(tempRes);

    } catch (error) {
        console.error(error);
        flashMessage(error.message, 'error');
        return false;

    } finally {
        controls.data('waspBusy', false);
    }

    if (!modal.hasClass('show')) {
        return false;
    }

    const draw = () => {
        if (
            modal.hasClass('show') &&
            !controls.data('waspBusy')
        ) {
            expand_health_wasp_charts(
                container,
                tempRes
            );
        }
    };

    expandModalCharts(
        contID,
        expand_health_wasp_charts,
        tempRes
    );

    purgePlotlyChartExpandModal(contID);
    $(`#rangeselector-${contID}`).show();

    let revision = 0;

    controls.on(
        'change.healthWaspCalculation',
        [
            `#${prefix}-timescale`,
            `#${prefix}-base-start`,
            `#${prefix}-base-end`,
            `#${prefix}-base-min`
        ].join(','),
        async () => {
            const current = ++revision;
            controls.data('waspBusy', true);

            try {
                const ready = await setHealthWaspDateCalendars(
                    tempRes,
                    prefix
                );

                if (current !== revision) {
                    return;
                }

                if (ready) {
                    await setHealthWaspExpandedControls(tempRes);
                }

                if (current !== revision) {
                    return;
                }

                controls.data('waspBusy', false);

                if (ready) {
                    draw();
                }

            } catch (error) {
                if (current === revision) {
                    controls.data('waspBusy', false);
                    console.error(error);
                    flashMessage(error.message, 'error');
                }
            }
        }
    );


    const redraw = () => {
        if (
            !modal.hasClass('show') ||
            controls.data('waspBusy')
        ) {
            return;
        }

        maproomDB.getData('ts_health_wasp', data => {
            if (data) {
                expand_health_display_wasp(data, container);
            }
        });
    };

    controls.on(
        'change.healthWaspExpanded',
        `#${prefix}-area`,
        draw
    );

    controls.on(
        'change.healthWaspExpanded',
        [
            `#${prefix}-comparison-start`,
            `#${prefix}-comparison-end`,
            `#${prefix}-comparison-month-calendar`,
            `#${prefix}-startdate-calendar`,
            `#${prefix}-enddate-calendar`
        ].join(','),
        redraw
    );


    $(`#plotly-replot-${contID}`)
        .off('click.healthWaspExpand')
        .on('click.healthWaspExpand', draw);

    $(`#plotly-download-${contID}`)
        .off('click.healthWaspExpand')
        .on('click.healthWaspExpand', () => {
            downloadPlotlyImageJPG(container);
        });
}

