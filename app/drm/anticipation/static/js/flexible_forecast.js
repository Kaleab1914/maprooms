$(document).ready(async function() {
    $('[data-bs-toggle="tooltip"]').tooltip();
    const tempRes = 'seasonal';
    const map = createLeafletTileLayer('div-map-container', MTO_INIT);
    const mapOptions = {};

    $('#div-map-time-navigation')
        .removeClass('d-flex')
        .addClass('d-none');

    try {
        const result = await setOffCanvasSeasFcstMapControl(tempRes);

        if (!result || result.status !== 0) {
            return;
        }
    } catch (error) {
        console.error('DRM forecast initialization failed:', error);

        flashMessage(
            'Unable to load the seasonal forecast controls.',
            'error'
        );
        return;
    }

    $('#support-spatial-average')
        .val('gridpoint')
        .prop('disabled', true);

    $('#list-spatial-average')
        .prop('disabled', true);

    function displayCharts(res) {
        preview_seasfcst_charts_proba(
            res,
            ['div-chart-poe', 'div-chart-pdf']
        );
    }

    function refreshForecast() {
        displayClimateSeasFcstMap(
            tempRes,
            mapOptions,
            map
        );

        displayCharts(tempRes);
    }

    $('#map-control-offcanvas-dataselect')
        .off('hidden.bs.offcanvas.drmFlexibleForecast')
        .on(
            'hidden.bs.offcanvas.drmFlexibleForecast',
            refreshForecast
        );

    $('#map-control-redraw')
        .off('click.drmFlexibleForecast')
        .on(
            'click.drmFlexibleForecast',
            refreshForecast
        );

    displayClimateSeasFcstMap(
        tempRes,
        mapOptions,
        map
    );

    mapClickLayersSpatialAverage(
        displayCharts,
        tempRes,
        map
    );
});