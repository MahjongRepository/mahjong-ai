$(document).ready(function () {
    var params = new URLSearchParams(window.location.search);
    var hand_id = params.get('hand');
    if (hand_id) {
        var url = '/data/' + hand_id;
        $.get(url, function (data) {
            var log_link = 'http://tenhou.net/0/?log=' + data['log_id'];
            log_link += '&tw=' + data['player_seat'];
            log_link += '&ts=' + data['hand_number'];

            $('#log_link').attr('href', log_link);

            var html = '';
            $.each(data['player_hand'], function (index, value) {
                html += tile_template.replace('{placeholder}', tiles_map[value]);
            });
            $('#hand').html(html);

            html = '';
            $.each(data['waiting'], function (index, value) {
                html += tile_template.replace('{placeholder}', tiles_map[value]);
            });
            $('#waiting').html(html);

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
    0: 'm1',
    1: 'm2',
    2: 'm3',
    3: 'm4',
    4: 'm5',
    5: 'm6',
    6: 'm7',
    7: 'm8',
    8: 'm9',
    9: 'p1',
    10: 'p2',
    11: 'p3',
    12: 'p4',
    13: 'p5',
    14: 'p6',
    15: 'p7',
    16: 'p8',
    17: 'p9',
    18: 's1',
    19: 's2',
    20: 's3',
    21: 's4',
    22: 's5',
    23: 's6',
    24: 's7',
    25: 's8',
    26: 's9',
    27: 'tan',
    28: 'nan',
    29: 'xia',
    30: 'pei',
    31: 'chun',
    32: 'haku',
    33: 'hatsu'
};