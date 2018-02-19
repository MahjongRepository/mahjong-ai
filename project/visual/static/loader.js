$(document).ready(function () {
    var params = new URLSearchParams(window.location.search);
    var hand_id = params.get('hand');
    if (hand_id) {
        var url = '/data/' + hand_id;
        $.get(url, function (data) {
            var log_link = 'http://tenhou.net/0/?log=' + data['log_id'];
            log_link += '&tw=' + data['player_seat'];
            log_link += '&ts=' + data['step'];

            $('#log_link').attr('href', log_link);

            $('#round_wind').text(winds[data.round_wind]);
            $('#player_wind').text(winds[data.player_wind]);

            var html = '';
            $.each(data['player_hand'], function (index, value) {
                html += tile_template.replace('{placeholder}', get_tile_name(value));
            });
            $('#hand').html(html);

            html = '';
            $.each(data['dora_indicators'], function (index, value) {
                html += tile_template.replace('{placeholder}', get_tile_name(value));
            });
            $('#dora').html(html);

            html = '';
            $.each(data['melds'], function (index, meld) {
                html += '<div class="mr">';
                $.each(meld['tiles'], function (index, value) {
                    html += tile_template.replace('{placeholder}', get_tile_name(value));
                });
                html += '</div>';
            });

            if (html.length) {
                $('#melds').show();
                $('#melds_content').html(html);
            }

            html = '';
            $.each(data['waiting'], function (index, value) {
                html += '<div style="margin-bottom: 10px">';
                html += tile_template.replace('{placeholder}', get_tile_name(value.tile));
                if (value.han) {
                    html += ' <span>' + value.han + ' han ' + value.fu + ' fu ' + '</span>';
                    html += '<span>' + value.cost + '</span>';
                } else {
                    html += ' <span>can\'t win</span>';
                }

                html += '</div>';
            });
            $('#waiting').html(html);

            html = '';
            $.each(data['discards'], function (index, value) {
                var template = tile_template.replace('{placeholder}', get_tile_name(value.tile));

                // player called riichi, let's rotate tile
                if (index + 1 === data['discards'].length && data.after_riichi) {
                    template = template.replace('{classes}', 'rotate');
                }

                if (value.after_meld) {
                    template = template.replace('{classes}', 'after-meld');
                }

                if (value.is_tsumogiri) {
                    template = template.replace('{classes}', 'tsumogiri');
                }

                html += template;
            });
            $('#discards').html(html);
        })
    }
});

function get_tile_name(tile_136) {
    if (tile_136 === 16) {
        return 'ma'
    }

    if (tile_136 === 52) {
        return 'pa'
    }

    if (tile_136 === 88) {
        return 'sa'
    }

    return tiles_map[Math.floor(tile_136 / 4)]
}

var winds = {
    27: '東',
    28: '南',
    29: '西',
    30: '北'
};

var tile_template = '<svg class="tile {classes}"><use class="face" xlink:href="/static/tiles.svg#{placeholder}"></use></svg>';

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