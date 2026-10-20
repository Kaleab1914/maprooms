$(document).ready(function() {
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
        .forEach(element => new bootstrap.Tooltip(element));

    const map = createLeafletTileLayer('div-map-container', MTO_INIT);

    const options = {};
    const tempRes = 'seasonal';
    const prefix = `${tempRes}-model-proj`;

    // hide map navigation
    $('#container-map-navigation').hide();

    setOffCanvasMapControlSeasonalProjection(tempRes, prefix);

    $(`#${prefix}-scenario`).val(
        PROJECTION_DEFAULTS.scenarios.default
    );

    $(`#${prefix}-change-signal`).val(
        PROJECTION_DEFAULTS.change_signal.default
    );

    const redraw = () => {
        displayClimateProjectionAgreementMap(options, map);
    };

    $('#map-control-redraw')
        .on('click.modelAgreement', redraw);

    $('#map-control-offcanvas-dataselect')
        .on('hidden.bs.offcanvas.modelAgreement', redraw);

    redraw();
});