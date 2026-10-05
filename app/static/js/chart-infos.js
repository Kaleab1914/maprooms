
// shown in the chart information dialogs
const CHART_INFOS = {};

function saveChartInfo(container, query, data) {
    CHART_INFOS[container] = { query: query, data: data };

    
    $('.plotly-chart-info-dialog')
        .filter((i, el) => $(el).data('chartContainer') === container)
        .filter(':visible')
        .each(function() {
            fillPlotlyChartInfoDialog($(this), container);
        });
}

// Dialog box: chart info
function buildPlotlyChartInfoDialog(dialogID) {
    return $('<div>', {
        id: dialogID,
        class: 'container-fluid dialog-box-settings plotly-chart-settings-dialog plotly-chart-info-dialog',
        role: 'dialog',
        'aria-modal': 'true',
        'aria-labelledby': `${dialogID}-title`
    }).append(
        $('<div>', { class: 'row m-2' }).append(
            $('<div>', { class: 'col-sm-11 d-flex justify-content-start' }).append(
                $('<span>', {
                    id: `${dialogID}-title`,
                    class: 'fw-bolder',
                    text: JS_TEXT.chart_info.title
                })
            ),
            $('<div>', { class: 'col-sm-1 d-flex justify-content-end' }).append(
                $('<button>', {
                    id: `${dialogID}-close-1`,
                    type: 'button',
                    class: 'btn btn-md position-absolute top-0 end-0 me-1 p-1',
                    title: JS_TEXT.chart_info.close,
                    'aria-label': JS_TEXT.chart_info.close
                }).append($('<i>', { class: 'bi bi-x-circle-fill' }))
            ),
            $('<hr>', { class: 'w-100' })
        ),
        $('<div>', {
            id: `${dialogID}-body`,
            class: 'container mt-2 mb-1 mx-0 px-2 py-2'
        }),
        $('<div>', { class: 'd-flex justify-content-end m-2' }).append(
            $('<button>', {
                id: `${dialogID}-close-2`,
                type: 'button',
                class: 'btn btn-sm btn-primary',
                text: JS_TEXT.chart_info.close
            })
        )
    );
}

// opens the info dialog of the chart drawn in container, in host
function openPlotlyChartInfoDialog(dialogID, container, host) {
    let dialog = $(document.getElementById(dialogID));

    if (!dialog.length) {
        dialog = buildPlotlyChartInfoDialog(dialogID);
        dialog.data('chartContainer', container);
        dialog
            .find(`#${dialogID}-close-1, #${dialogID}-close-2`)
            .on('click', function() {
                dialog.fadeOut(200);
            });
    }
    if (!dialog.parent().is(host)) {
        dialog.appendTo(host);
    }

    fillPlotlyChartInfoDialog(dialog, container);
    dialog.fadeIn(200);
}

function fillPlotlyChartInfoDialog(dialog, container) {
    const body = dialog.find(`#${dialog.attr('id')}-body`).empty();
    const info = CHART_INFOS[container];
    const sections = info ? getChartInfoSections(info.query, info.data) : [];

    if (!sections.length) {
        body.append($('<p>', {
            class: 'mb-0',
            text: info ? JS_TEXT.chart_info.no_info : JS_TEXT.chart_info.no_chart
        }));
        return;
    }
    sections.forEach(section => body.append(buildChartInfoSection(section)));
}


function buildChartInfoSection(section) {
    const list = $('<dl>', { class: 'row mb-0' });
    section.rows.forEach(([label, value]) => {
        const lines = [].concat(value).map(line => $('<div>', { text: line }));
        list.append(
            $('<dt>', { class: 'col-sm-5 fw-normal text-body-secondary', text: label }),
            $('<dd>', { class: 'col-sm-7 mb-1' }).append(lines)
        );
    });

    const div = $('<div>', { class: 'mb-3' }).append(
        $('<div>', { class: 'fw-bold mb-1', text: section.title }),
        list
    );
    if (section.note) {
        div.append($('<div>', { class: 'small text-body-secondary', text: section.note }));
    }
    return div;
}


function getChartInfoSections(query, data) {
    const text = JS_TEXT.chart_info;
    return [
        { title: text.location, rows: getChartInfoLocation(query) },
        { title: text.data, rows: getChartInfoData(query, data) },
        { title: text.statistics, rows: getChartInfoStatistics(data) },
        Object.assign({ title: text.trend }, getChartInfoTrend(data))
    ].filter(section => section.rows.length > 0);
}

// grid point: its coordinates; polygon: its subdivision type and name
function getChartInfoLocation(query) {
    const text = JS_TEXT.chart_info;

    if (query.geomExtract === 'points') {
        const point = query.pointsList[0];
        return [
            [text.longitude, Number(point.lon).toFixed(6)],
            [text.latitude, Number(point.lat).toFixed(6)]
        ];
    }

    if (query.geomExtract === 'polygons') {
        const subdiv = Object.values(LAYERS.subdivision).find(s =>
            s.file === query.shpFile && s.field === query.shpField
        );
        if (subdiv === undefined) {
            return [[text.name, query.Poly]];
        }
        const typeLabel = text.subdivision_type[subdiv.group] ||
            LAYERS.subdivision_group[subdiv.group];
        return [
            [typeLabel, subdiv.name],
            [text.name, query.Poly]
        ];
    }

    return [];
}

function getChartInfoData(query, data) {
    const text = JS_TEXT.chart_info;
    const rows = [];

    if (query.dataset) {
        rows.push([text.dataset, query.dataset]);
    }

    const variable = data && data.info && data.info.var;
    if (variable && variable.name) {
        const name = variable.units ?
            `${variable.name} (${variable.units})` :
            variable.name;
        rows.push([text.variable, name]);
    }

    const season = formatChartInfoSeason(query);
    if (season) {
        rows.push([text.season, season]);
    }

    const period = getChartInfoPeriod(query, data);
    if (period) {
        rows.push(
            [text.start_date, period.start],
            [text.end_date, period.end]
        );
    }

   
    if (query.minYear !== undefined) {
        rows.push([text.base_period, `${query.startYear} - ${query.endYear}`]);
    }

    return rows;
}


function formatChartInfoSeason(query) {
    const locale = LANG_USER.selected.locale;

    
    if (query.fullYearTS) {
        return null;
    }

    if (Number.isInteger(query.seasStart) && Number.isInteger(query.seasLength)) {
        const month = m => new Date(2000, m - 1, 1)
            .toLocaleString(locale, { month: 'short' });
        if (query.seasLength === 1) {
            return month(query.seasStart);
        }
        const end = (query.seasStart + query.seasLength - 2) % 12 + 1;
        return `${month(query.seasStart)} - ${month(end)}`;
    }

    if (Number.isInteger(query.startMonth) && Number.isInteger(query.endMonth)) {
        const day = (m, d) => new Date(2000, m - 1, d)
            .toLocaleString(locale, { day: 'numeric', month: 'short' });
        return `${day(query.startMonth, query.startDay)} - ${day(query.endMonth, query.endDay)}`;
    }

    return null;
}


function getChartInfoPeriod(query, data) {
    if (query.startDate !== undefined && query.endDate !== undefined) {
        return {
            start: formatChartInfoDate(query.startDate, query.temporalRes),
            end: formatChartInfoDate(query.endDate, query.temporalRes)
        };
    }

    if (query.startYear !== undefined) {
        if (query.minYear !== undefined) {
            return null;
        }
        return { start: String(query.startYear), end: String(query.endYear) };
    }

    
    const time = data && data.time;
    if (Array.isArray(time) && time.length > 0 && Number.isInteger(time[0])) {
        return { start: String(time[0]), end: String(time.at(-1)) };
    }

    return null;
}


function formatChartInfoDate(value, timeRes) {
    const locale = LANG_USER.selected.locale;
    const parts = String(value).split('-');
    if (parts.length === 1) {
        return parts[0];
    }

    const [year, month, day] = parts.map(Number);
    const monthName = new Date(year, month - 1, 1)
        .toLocaleString(locale, { month: 'long' });
    if (parts.length === 2) {
        return `${monthName} ${year}`;
    }


    if (parts[2].length === 1) {
        return `dekad-${day} ${monthName} ${year}`;
    }
    if (timeRes === 'dekadal') {
        const dekad = day <= 10 ? 1 : (day >= 21 ? 3 : 2);
        return `dekad-${dekad} ${monthName} ${year}`;
    }
    return new Date(year, month - 1, day).toLocaleDateString(locale, {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });
}


function getChartInfoStatistics(data) {
    if (!data || !data.stats || !data.info) {
        return [];
    }

    const text = JS_TEXT.chart_info;
    const stats = data.stats;
    const format = getChartInfoValueFormat(data);
    const terciles = [
        `${format(stats.tercile1)} (${text.tercile_lower})`,
        `${format(stats.tercile2)} (${text.tercile_upper})`
    ];
    return [
        [text.mean, format(stats.mean)],
        [text.median, format(stats.median)],
        [text.terciles, terciles]
    ];
}


function getChartInfoTrend(data) {
    if (!data || !data.coeffs || !data.info) {
        return { rows: [] };
    }

    const text = JS_TEXT.chart_info;
    const coeffs = data.coeffs;
    const slope = formatChartInfoNumber(coeffs.slope, 3);
    const sign = coeffs.intercept < 0 ? '-' : '+';
    const intercept = formatChartInfoNumber(Math.abs(coeffs.intercept), 3);

    
    const variable = data.info.var;
    const start = getChartInfoRainySeasonStart(data);
    let yText;
    if (start) {
        const day = formatTickTextRainySeason([0], start, variable)[0];
        yText = `${text.trend_y_days} ${day}`;
    } else {
        yText = variable.units ?
            `${variable.name} (${variable.units})` :
            variable.name;
    }

    return {
        rows: [
            [text.trend_equation, `y = ${slope} x ${sign} ${intercept}`],
            [text.r_squared, `R² = ${formatChartInfoNumber(coeffs.r_squared, 3)}`]
        ],
        note: `${text.trend_x}, ${text.trend_y} ${yText}`
    };
}


function getChartInfoValueFormat(data) {
    const variable = data.info.var;
    const start = getChartInfoRainySeasonStart(data);
    if (start) {
        return value => formatTickTextRainySeason([value], start, variable)[0];
    }
    return value => {
        const number = formatChartInfoNumber(value, 2);
        return variable.units ? `${number} ${variable.units}` : number;
    };
}


function getChartInfoRainySeasonStart(data) {
    const variable = data.info.var;
    if (!['onset', 'cessation'].includes(variable.type) || !Array.isArray(data.start)) {
        return null;
    }
    return data.start.find(value => value !== null) || null;
}


function formatChartInfoNumber(value, digits) {
    const rounded = Number(value.toFixed(digits));
    if (rounded === 0 && value !== 0) {
        return String(Number(value.toPrecision(2)));
    }
    return String(rounded);
}



function enablePlotlyChartExpandInfoDialogs() {
    const expandInfoButtonSelector = 'button.modebar-btn[id^="plotly-chart-info-"]';

    $(document)
        .off('click.plotlyChartExpandInfo', expandInfoButtonSelector)
        .on('click.plotlyChartExpandInfo', expandInfoButtonSelector, function() {
            const chartID = this.id.replace('plotly-chart-info-', '');
            const modalHost = $(this).closest('.modal');
            openPlotlyChartInfoDialog(
                `plotly-chart-expand-info-dialog-${chartID}`,
                `container-chart-${chartID}`,
                modalHost.length ? modalHost : $(document.body)
            );
        });
}

function enablePlotlyChartPreviewInfoDialogs() {
    const previewInfoButtonSelector = 'button.btn-preview-chart[id^="info-preview-"]';

    $(document)
        .off('click.plotlyChartPreviewInfo', previewInfoButtonSelector)
        .on('click.plotlyChartPreviewInfo', previewInfoButtonSelector, function() {
            const chartID = this.id.replace('info-preview-', '');
            openPlotlyChartInfoDialog(
                `plotly-chart-preview-info-dialog-${chartID}`,
                chartID,
                $(document.body)
            );
        });
}

$(function() {
    enablePlotlyChartExpandInfoDialogs();
    enablePlotlyChartPreviewInfoDialogs();
});
