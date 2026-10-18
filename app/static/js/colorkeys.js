function displayColorBar(ckeys, direction, map) {
    const options = {
        id: 'table-colorkeyH-id',
        position: 'bottomright'
    };
    const colorkeyFun = direction === 'vertical' ? createColorKeyVE : createColorKeyH;

    addLControlColorBar(colorkeyFun(ckeys), options, map);

    $('.leaflet-colorbar').css('background-color', '#f4f4f4');

    if (direction === 'vertical') {
        $('.leaflet-right .leaflet-colorbar').css({
            'padding-left': '5px',
            'margin-right': '5px',
            'margin-bottom': '5px',
            'line-height': '70%'
        });
        const map_container = $('#' + map._container.id);
        const ch = Math.round(map_container.height() / 7);
        $('.leaflet-colorbar .ckeyvE').css({
            'width': '60px',
            'height': ch + 'px',
        });
        $('.leaflet-colorbar .ckeyvE-label').css({
            'font-size': 10,
            'color': 'black'
        });
        $('.leaflet-colorbar .ckeyvE-title').css('color', 'black');
        $('.leaflet-colorbar td.ckeyvE-tick').css('width', '5px');
    } else {
        $('.leaflet-right .leaflet-colorbar').css({
            'margin-right': '5px',
            'margin-bottom': '1px',
            'padding-right': '3px',
            'padding-left': '3px'
        });
        $('.leaflet-colorbar .ckeyh').css({
            'width': '290px',
            'height': '55px'
        });
        $('.leaflet-colorbar .ckeyh-title').css('color', 'black');
        $('.leaflet-colorbar .ckeyh-label').css({
            'font-size': 10,
            'color': 'black'
        });
        $('.leaflet-colorbar tr.ckeyh-tick').css('height', '5px');
    }
}

function createColorKeyH(ckey) {
    var ckey = makeCopy(ckey);
    var nc = ckey.colors.length;
    var nl = ckey.labels.length;
    var ntd = 2 * (nc - 1);

    var table = $('<table>').addClass('ckeyh');

    var row0 = $('<tr>').addClass('ckeyh-title');

    ///////
    if (
        Array.isArray(ckey.categories)
        && ckey.categories.length > 0
    ) {
        return createCategoricalColorKeyH(ckey);
    }
    ///////
    
    $('<td>').attr('colspan', ntd)
        .html(ckey.title).appendTo(row0);
    table.append(row0);

    var row1 = $('<tr>').addClass('ckeyh-color');
    $('<td>').css('background-color', ckey.colors[0]).appendTo(row1);
    for (j = 1; j < nc - 1; ++j) {
        $('<td>').attr('colspan', 2)
            .css('background-color', ckey.colors[j])
            .appendTo(row1);
    }
    $('<td>').css('background-color', ckey.colors[nc - 1]).appendTo(row1);
    table.append(row1);

    var row2 = $('<tr>').addClass('ckeyh-tick');
    row2.append($('<td>'));
    for (j = 1; j < nc - 1; ++j) {
        $('<td>').attr('colspan', 2).appendTo(row2);
    }
    row2.append($('<td>'));
    table.append(row2);

    var row3 = $('<tr>').addClass('ckeyh-label');
    for (j = 0; j < nl; ++j) {
        $('<td>').attr('colspan', 2)
            .text(ckey.labels[j])
            .appendTo(row3);
    }
    table.append(row3);

    var row4 = $('<tr>');
    for (j = 0; j < ntd; ++j) {
        var col = $('<td>').html('&nbsp;');
        col.css({
            'text-align': 'center',
            'line-height': '0px',
            'margin': 0,
            'padding': 0
        });
        row4.append(col);
    }
    table.append(row4);

    return table;
}

function imageColorKeyH(ckey) {
    var ckey = makeCopy(ckey);
    var table = $('<table>').addClass('rckeyh');
    var row0 = $('<tr>').addClass('rckeyh-title');
    $('<td>').text(ckey.title).appendTo(row0);
    table.append(row0);

    var row1 = $('<tr>').addClass('rckeyh-color');
    $('<td>').css({
            'margin': 0,
            'padding': 0
        })
        .prepend($('<img>', { src: ckey['png'] }))
        .appendTo(row1);
    table.append(row1);

    return table;
}

function rasterColorKeyH(ckey) {
    var ckey = makeCopy(ckey);
    var nl = ckey.labels.length;
    var ntd = 2 * nl;

    var table = $('<table>').addClass('rckeyh');

    var row0 = $('<tr>').addClass('rckeyh-title');
    $('<td>').attr('colspan', ntd)
        .html(ckey.title).appendTo(row0);
    table.append(row0);

    var row1 = $('<tr>').addClass('rckeyh-color');
    $('<td>').html('&nbsp;').appendTo(row1);
    var td_img = $('<td>').attr('colspan', ntd - 2);
    td_img.css({
        'margin': 0,
        'padding': 0
    }).appendTo(row1);
    var key = ['png', 'src'].filter(x => ckey[x])[0];
    td_img.prepend($('<img>', { src: ckey[key] }));

    $('<td>').html("&nbsp;").appendTo(row1);
    table.append(row1);

    var row2 = $('<tr>').addClass('rckeyh-tick');
    row2.append($('<td>'));
    for (var j = 1; j < nl; ++j) {
        $('<td>').attr('colspan', 2).appendTo(row2);
    }
    row2.append($('<td>'));
    table.append(row2);

    var row3 = $('<tr>').addClass('rckeyh-label');
    for (var j = 0; j < nl; ++j) {
        $('<td>').attr('colspan', 2)
            .text(ckey.labels[j])
            .appendTo(row3);
    }
    table.append(row3);

    var row4 = $('<tr>');
    for (j = 0; j < ntd; ++j) {
        var col = $('<td>').html('&nbsp;');
        col.css({
            'text-align': 'center',
            'line-height': '0px',
            'margin': 0,
            'padding': 0
        });
        row4.append(col);
    }
    table.append(row4);

    return table;
}

function createColorKeyVE(ckey, reverse = true) {
    var ckey = makeCopy(ckey);
    if (reverse) {
        ckey.labels = ckey.labels.reverse();
        ckey.colors = ckey.colors.reverse();
    }
    var nc = ckey.colors.length;
    var nl = ckey.labels.length;
    var ntr = 2 * (nc - 1);

    var kol = [];
    for (j = 0; j < nc; ++j) {
        if (j === 0 || j === nc - 1) {
            kol.push(ckey.colors[j]);
        } else {
            kol.push(ckey.colors[j]);
            kol.push(ckey.colors[j]);
        }
    }

    var table = $('<table>').addClass('ckeyvE');

    for (j = 1; j <= ntr; ++j) {
        var row = $('<tr>');

        var td_col = $('<td>').addClass('ckeyvE-color')
            .css('background-color', kol[j - 1]).appendTo(row);

        var td_tck = $('<td>').addClass('ckeyvE-tick')
            .html('&nbsp;').appendTo(row);

        if (j === 1) {
            td_col.css('border-top', '1px solid black');
        }
        if (j === ntr) {
            td_col.css('border-bottom', '1px solid black');
        }

        if (j % 2 != 0) {
            $('<td>').addClass('ckeyvE-label')
                .attr('rowspan', 2)
                .text(ckey.labels[Math.floor(j / 2)])
                .appendTo(row);

            td_tck.css('border-bottom', '1px solid black');
        }

        if (j === 1) {
            $('<td>').addClass('ckeyvE-title')
                .attr('rowspan', ntr)
                .text(ckey.title).appendTo(row);
        }

        table.append(row);
    }

    return table;
}

///////

function createCategoricalColorKeyH(ckey) {
    const categories = ckey.categories;
    const table = $('<table>').addClass('ckeyh');

    const titleRow = $('<tr>').addClass('ckeyh-title');

    $('<td>')
        .attr('colspan', categories.length)
        .text(ckey.title)
        .appendTo(titleRow);

    table.append(titleRow);

    const colorRow = $('<tr>').addClass('ckeyh-color');
    const labelRow = $('<tr>').addClass('ckeyh-label');

    categories.forEach(category => {
        $('<td>')
            .css({
                'background-color': category.color,
                'height': '12px',
                'border': '1px solid #999'
            })
            .appendTo(colorRow);

        const label = $('<td>').css({
            'text-align': 'center',
            'padding': '2px 4px',
            'white-space': 'nowrap'
        });

        $('<div>').text(category.label).appendTo(label);
        $('<div>').text(category.range).appendTo(label);

        labelRow.append(label);
    });

    table.append(colorRow, labelRow);

    return table;
}
