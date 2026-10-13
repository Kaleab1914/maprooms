$(document).ready(function() {
    // $('[data-bs-toggle="tooltip"]').tooltip();
    const tTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tTriggerList].map(t => new bootstrap.Tooltip(t));

    let map = createLeafletTileLayer('div-map-container', MTO_INIT);

    // hide map time navigation
    $('#div-map-time-navigation').removeClass('d-flex').addClass('d-none');

    setOffCanvasMapControlsDrmExtRain('daily');
    //setOffCanvasMapControlsDrmExtRain_pdf('daily');

    ////////////
    // Modal Expand Charts

    $('.daily-proba-select2').select2({
        minimumResultsForSearch: -1,
        dropdownParent: $('#daily-drmExt-cdf-control')
    });
    $('#btn-div-chart-cdf').on('click', () => {
        setAnalysisExpandModalDrmExt_cdf('daily', 'div-chart-cdf');
    });
    $('#btn-div-chart-pdf').on('click', () => {
        setAnalysisExpandModalDrmExt_pdf('daily', 'div-chart-pdf');
    });

    // for pdf

    $('.daily-pdf-select2').select2({
        minimumResultsForSearch: -1,
        dropdownParent: $('#daily-drmExt-pdf-control')
    });
    $('#btn-div-chart-cdf').on('click', () => {
        setAnalysisExpandModalDrmExt_cdf('daily', 'div-chart-cdf');
    });
    $('#btn-div-chart-pdf').on('click', () => {
        setAnalysisExpandModalDrmExt_pdf('daily', 'div-chart-pdf');
    });
    
    // Preview chart
    $('#daily-map-parameters')
        .off('change.drmPreview')
        .on('change.drmPreview', function() {
            preview_drmExt_display_charts('daily');
        });

    ////////////
    // initialize map
    const map_options = {};
    displayDrmAnalysisMap('daily', map_options, map);

    // display map when offcanvas hidden
    $('#map-control-offcanvas-dataselect').on('hidden.bs.offcanvas', () => {
        displayDrmAnalysisMap('daily', map_options, map);
    });

    // 
    $('#map-control-redraw').on('click', () => {
        displayDrmAnalysisMap('daily', map_options, map);
    });

    ///////////
    // display preview time series on click on map, or select polygon
    mapClickLayersSpatialAverage(preview_drmExt_display_charts, 'daily', map);

    $('#select-country-region').on('change', () => {
        mapClickLayersSpatialAverage(preview_drmExt_display_charts, 'daily', map);
    });

    $('#select-region-name').on('change', () => {
        mapClickLayersSpatialAverage(preview_drmExt_display_charts, 'daily', map);
    });
});