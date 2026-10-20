$(document).ready(function() {
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
        .forEach(element => new bootstrap.Tooltip(element));

    const map = createLeafletTileLayer("div-map-container", MTO_INIT);

    const options = {};
    const tempRes = "seasonal";
    const prefix = `${tempRes}-seasonal-proj`;

    // hide map time navigation
    $('#div-map-time-navigation').removeClass('d-flex').addClass('d-none');

    // Initialize map controls.
    setOffCanvasMapControlSeasonalProjection(tempRes);

    $(`#${prefix}-gcm`).val(
        PROJECTION_DEFAULTS.GCM.default
    );

    $(`#${prefix}-scenario`).val(
        PROJECTION_DEFAULTS.scenarios.default
    );

    /////
    $('#btn-div-chart-distribution-proj')
        .off('click.projectionExpand')
        .on('click.projectionExpand', () => {
            setProjectionExpandModalDistribution(
                tempRes,
                'div-chart-distribution-proj'
            );
        });


    $('#btn-div-chart-seasonal-proj')
        .off('click.projectionExpand')
        .on('click.projectionExpand', () => {
            setProjectionExpandModalSeries(
                tempRes,
                'div-chart-seasonal-proj'
            );
        });

    const resolution = {
        lon: '…',
        lat: '…'
    };

    $(`#${prefix}-gcm`).data(
        'projectionSpatialResolution',
        resolution
    );

    setSelectSpatialAverage(resolution);


    const redraw = () => {
        displayClimateProjectionSeasonalMap(options, map);
        preview_projection_display_charts(tempRes);
    };

    // Initial map display.
    displayClimateProjectionSeasonalMap(options, map);

    mapClickLayersSpatialAverage(
        preview_projection_display_charts,
        tempRes,
        map
    );

    $("#map-control-redraw")
        .on("click.seasonalProjection", redraw);

    $("#map-control-offcanvas-dataselect")
        .on("hidden.bs.offcanvas.seasonalProjection", redraw);

    //////////
    // resolution should be provided from data
    $('#list-spatial-average').select2({
        data: [{ id: 'grid', text: '2.50 x 2.50' }]
    });

    //// grid point only 
    $('#support-spatial-average').prop('disabled', true);
    $('#list-spatial-average').prop('disabled', true);
});