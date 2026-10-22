$(document).ready(async function() {
    $('[data-bs-toggle="tooltip"]').tooltip();
    let map = createLeafletTileLayer('div-map-container', MTO_INIT);

    // hide map time navigation
    $('#div-map-time-navigation')
        .removeClass('d-flex')
        .addClass('d-none');

    // offcanvas map controls
    await setOffCanvasSeasFcstMapControl('seasonal');

    ////////////
    // Modal Expand Charts
    $('.seasonal-ter-select2').select2({
        minimumResultsForSearch: -1,
        dropdownParent: $('#seasonal-ter-control')
    });
    $('#btn-div-chart-ter').on('click', async () => {
        await setAnalysisExpandModalSeasFcst(
            'seasonal', 'div-chart-ter', 'ter'
        );
    });

    $('.seasonal-cdf-select2').select2({
        minimumResultsForSearch: -1,
        dropdownParent: $('#seasonal-cdf-control')
    });
    $('#btn-div-chart-cdf').on('click', async () => {
        await setAnalysisExpandModalSeasFcst(
            'seasonal', 'div-chart-cdf', 'cdf'
        );
    });

    $('.seasonal-pdf-select2').select2({
        minimumResultsForSearch: -1,
        dropdownParent: $('#seasonal-pdf-control')
    });
    $('#btn-div-chart-pdf').on('click', async () => {
        await setAnalysisExpandModalSeasFcst(
            'seasonal', 'div-chart-pdf', 'pdf'
        );
    });

    ////////////
    // initialize map
    const map_options = {};
    displayClimateSeasFcstMap('seasonal', map_options, map);

    // display map when offcanvas hidden
    $('#map-control-offcanvas-dataselect').on('hidden.bs.offcanvas', () => {
        displayClimateSeasFcstMap('seasonal', map_options, map);
    });

    // 
    $('#map-control-redraw').on('click', () => {
        displayClimateSeasFcstMap('seasonal', map_options, map);
    });

    ///////////
    // display preview time series on click on map
    mapClickLayersSpatialAverage(preview_seasfcst_display_charts, 'seasonal', map);

    //// grid point only 
    $('#support-spatial-average').prop('disabled', true);
    $('#list-spatial-average').prop('disabled', true);
});
