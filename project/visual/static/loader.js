$(document).ready(function () {
    var params = new URLSearchParams(window.location.search);
    var hand_id = params.get('hand');
    if (hand_id) {
        var url = '/data/' + hand_id;
        $.get(url, function (data) {
            var html = '';
            $.each(data['hand'], function (index, value) {
                html += tile_template.replace('{placeholder}', tiles_map[value]);
            });
            $('#hand').html(html);

            html = '';
            $.each(data['discards'], function (index, value) {
                html += tile_template.replace('{placeholder}', tiles_map[value.tile]);
            });
            $('#discards').html(html);
        })
    }
});

var tile_template = '<svg class="tile"><use class="face" xlink:href="/static/tiles.svg#{placeholder}"></use></svg>';

var tiles_map = {
    1: 'm1',
    2: 'm2',
    3: 'm3',
    4: 'm4',
    5: 'm5',
    6: 'm6',
    7: 'm7',
    8: 'm8',
    9: 'm9',
    10: 'p1',
    11: 'p2',
    12: 'p3',
    13: 'p4',
    14: 'p5',
    15: 'p6',
    16: 'p7',
    17: 'p8',
    18: 'p9',
    19: 's1',
    20: 's2',
    21: 's3',
    22: 's4',
    23: 's5',
    24: 's6',
    25: 's7',
    26: 's8',
    27: 's9',
    28: 'tan',
    29: 'nan',
    30: 'xia',
    31: 'pei',
    32: 'chun',
    33: 'haku',
    34: 'hatsu'
};