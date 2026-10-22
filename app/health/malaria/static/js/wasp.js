$(document).ready(async function() {
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
        .forEach(element => {
            bootstrap.Tooltip.getOrCreateInstance(element);
        });

    const tempRes = 'monthly';
    const prefix = `${tempRes}-wasp-map`;

    const map = createLeafletTileLayer('div-map-container',MTO_INIT);

    const mapOptions = {};
    let refreshVersion = 0;
    const previewHolder = $('#div-chart-wasp')
        .addClass('position-relative')[0];

    const mapPreparing = new Spinner(spinnerMapOptions());
    const previewPreparing = new Spinner(spinnerChartOptions());

    mapPreparing.spin(map.getContainer());
    previewPreparing.spin(previewHolder);
    const initialization = setOffCanvasMapControlHealthWasp(tempRes);


    async function refreshWasp() {
        const version = ++refreshVersion;

        mapPreparing.spin(map.getContainer());
        previewPreparing.spin(previewHolder);

        try {
            const initialized = await initialization;

            if (!initialized || version !== refreshVersion) {
                return;
            }

            const ready = await setHealthWaspDateCalendars(
                tempRes,
                prefix
            );

            if (!ready || version !== refreshVersion) {
                return;
            }

            displayHealthWaspMap(tempRes, mapOptions, map);
            preview_health_wasp_charts(tempRes);

        } finally {
            if (version === refreshVersion) {
                mapPreparing.stop();
                previewPreparing.stop();
            }
        }
    }


    $('#map-control-offcanvas-dataselect')
        .off('hidden.bs.offcanvas.healthWasp')
        .on(
            'hidden.bs.offcanvas.healthWasp',
            refreshWasp
        );

    $('#map-control-redraw')
        .off('click.healthWasp')
        .on('click.healthWasp', refreshWasp);

    $('#btn-div-chart-wasp')
        .off('click.healthWaspExpand')
        .on('click.healthWaspExpand', () => {
            setHealthExpandModalWasp(
                tempRes,
                'div-chart-wasp'
            );
        });

    $('#input-time-navigation')
        .off('blur.healthWasp')
        .on('blur.healthWasp', () => {
            if (setHealthWaspMapDate(tempRes)) {
                refreshWasp();
            }
        });

    $('#prev-time-navigation')
        .off('click.healthWasp')
        .on('click.healthWasp', () => {
            if (setHealthWaspMapDate(tempRes, -1)) {
                refreshWasp();
            }
        });

    $('#next-time-navigation')
        .off('click.healthWasp')
        .on('click.healthWasp', () => {
            if (setHealthWaspMapDate(tempRes, 1)) {
                refreshWasp();
            }
        });


    // $(`#${tempRes}-wasp-chart-area`)
    //     .off('change.healthWaspArea')
    //     .on('change.healthWaspArea', () => {
    //         preview_health_wasp_charts(tempRes);
    //     });


    try {
        const initialized = await initialization;

        if (initialized && refreshVersion === 0) {
            displayHealthWaspMap(tempRes, mapOptions, map);
            preview_health_wasp_charts(tempRes);
        }

    } finally {
        if (refreshVersion === 0) {
            mapPreparing.stop();
            previewPreparing.stop();
        }
    }
});
