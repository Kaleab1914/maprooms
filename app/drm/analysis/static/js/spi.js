$(document).ready(function() {
    $('[data-bs-toggle="tooltip"]').tooltip();
    let map = createLeafletTileLayer('div-map-container', MTO_INIT);

    // offcanvas map controls
    setOffCanvasMapControlDrmSpiAnalysis('seasonal');

    // Expand chart

    $('.seasonal-spei-select2').select2({
        minimumResultsForSearch: -1,
        dropdownParent: $('#seasonal-spei-control')
    });

    $('#btn-div-chart-spi').on('click', () => {
        setAnalysisExpandModalSPEI('seasonal', 'div-chart-spi');
    });


    // Preview chart
    $('#daily-map-parameters')
        .off('change.drmPreview')
        .on('change.drmPreview', function() {
            preview_drmExt_display_charts('seasonal');
        });


    ////////////
    $('#input-time-navigation').on('blur', async () => {
        const ret = await setMapDatesNavInput('seasonal');
        if (ret) {
            displayDrmAnalysisMapSPI('seasonal', map_options, map);
        }
    });

    $('#prev-time-navigation').on('click', async () => {
        const ret = await setMapDatesNavPrev('seasonal');
        if (ret) {
            displayDrmAnalysisMapSPI('seasonal', map_options, map);
        }
    });

    $('#next-time-navigation').on('click', async () => {
        const ret = await setMapDatesNavNext('seasonal');
        if (ret) {
            displayDrmAnalysisMapSPI('seasonal', map_options, map);
        }
    });


    // INitialize map
    const map_options = {};
    displayDrmAnalysisMapSPI('seasonal', map_options, map);
    //displayDrmAnalysisMapSPI('seasonal');

    // display map when offcanvas hidden
    $('#map-control-offcanvas-dataselect').on('hidden.bs.offcanvas', () => {
        displayDrmAnalysisMapSPI('seasonal', map_options, map);
    });

    // 
    $('#map-control-redraw').on('click', () => {
        displayDrmAnalysisMapSPI('seasonal', map_options, map);
    });
});

