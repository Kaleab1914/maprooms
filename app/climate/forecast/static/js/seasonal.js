$(document).ready(function() {
    $('[data-bs-toggle="tooltip"]').tooltip();
    let map = createLeafletTileLayer('div-map-container', MTO_INIT);

    // hide map time navigation
    $('#div-map-time-navigation').removeClass('d-flex').addClass('d-none');

    // offcanvas map controls
    setOffCanvasSeasFcstMapControl('seasonal');

    ////////////
    // Modal Expand Charts


    ////////////
    // initialize map
    const map_options = {};
    setTimeout(() => {
        displayClimateSeasFcstMap('seasonal', map_options, map);
    }, 500);

    // display map when offcanvas hidden
    $('#map-control-offcanvas-dataselect').on('hidden.bs.offcanvas', () => {
        displayClimateSeasFcstMap('seasonal', map_options, map);
    });

    // 
    $('#map-control-redraw').on('click', () => {
        displayClimateSeasFcstMap('seasonal', map_options, map);
    });

    ////////////

    // resolution should be provided from data
    $('#list-spatial-average').select2({
        data: [{ id: 'grid', text: '0.25 x 0.25' }]
    });

    //// grid point only 
    $('#support-spatial-average').prop('disabled', true);
    $('#list-spatial-average').prop('disabled', true);
});