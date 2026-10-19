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

});