$(document).ready(function() {
    $('[data-bs-toggle="tooltip"]').tooltip();

    const map = createLeafletTileLayer('div-map-container', MTO_INIT);
    const map_options = {};

    // Initialize cotrol
    setOffCanvasMapControlDrmSpiAnalysis('seasonal');

    // Expanded chart
    $('.seasonal-spei-select2').select2({
        minimumResultsForSearch: -1,
        dropdownParent: $('#seasonal-spei-control')
    });

    $('#btn-div-chart-spi')
        .off('click.drmSpiExpand')
        .on('click.drmSpiExpand', () => {
            setAnalysisExpandModalSPEI('seasonal', 'div-chart-spi');
        });

    function refreshSpi() {
        displayDrmAnalysisMapSPI('seasonal', map_options, map);
        preview_drmSpi_display_charts('seasonal');
    }

    // Refresh 
    $('#map-control-offcanvas-dataselect')
        .on('hidden.bs.offcanvas', refreshSpi);

    $('#map-control-redraw').on('click', refreshSpi);

    // Refresh preview 
    $('#seasonal-map-date-length')
        .off('change.drmSpiPreview')
        .on('change.drmSpiPreview', () => {
            preview_drmSpi_display_charts('seasonal');
        });

    // Map date navigation next preview
    $('#input-time-navigation').on('blur', async () => {
        const valid = await setMapDatesNavInput('seasonal');
        if (valid) {
            refreshSpi();
        }
    });

    $('#prev-time-navigation').on('click', async () => {
        const valid = await setMapDatesNavPrev('seasonal');
        if (valid) {
            refreshSpi();
        }
    });

    $('#next-time-navigation').on('click', async () => {
        const valid = await setMapDatesNavNext('seasonal');
        if (valid) {
            refreshSpi();
        }
    });

    // Initial map
    displayDrmAnalysisMapSPI('seasonal', map_options, map);

    // Preview on map-point clicks
    mapClickLayersSpatialAverage(
        preview_drmSpi_display_charts,
        'seasonal',
        map
    );
});
