$(document).ready(async function() {
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
        .forEach(element => {
            bootstrap.Tooltip.getOrCreateInstance(element);
        });

    const tempRes = 'monthly';
    const prefix = `${tempRes}-spi-proj`;
    const map_options = {};

    const map = createLeafletTileLayer('div-map-container',MTO_INIT);

    $('#div-map-time-navigation')
        .removeClass('d-flex')
        .addClass('d-none');

    let refreshVersion = 0;

    const initialization = setOffCanvasMapControlSpiProjection(
        tempRes
    );

    async function refreshSpi() {
        const version = ++refreshVersion;

        await initialization;

        if (version !== refreshVersion) {
            return;
        }

        const valid = await setProjectionSpiDateCalendars(
            tempRes,
            prefix
        );

        if (!valid || version !== refreshVersion) {
            return;
        }

        displayClimateProjectionSpiMap(map_options, map);
        preview_projection_spi_charts(tempRes);
    }


    $('#map-control-offcanvas-dataselect')
        .off('hidden.bs.offcanvas.projectionSpi')
        .on('hidden.bs.offcanvas.projectionSpi', refreshSpi);

    $('#map-control-redraw')
        .off('click.projectionSpi')
        .on('click.projectionSpi', refreshSpi);

    $('#btn-div-chart-spi-proj')
        .off('click.projectionSpiExpand')
        .on('click.projectionSpiExpand', () => {
            setProjectionExpandModalSpi(
                tempRes,
                'div-chart-spi-proj'
            );
        });

    mapClickLayersSpatialAverage(
        preview_projection_spi_charts,
        tempRes,
        map
    );

    const initialized = await initialization;

    if (initialized && refreshVersion === 0) {
        displayClimateProjectionSpiMap(map_options, map);
        preview_projection_spi_charts(tempRes);
    }
});

