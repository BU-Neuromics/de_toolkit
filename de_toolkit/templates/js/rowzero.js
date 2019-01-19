var data = d.properties.zeros,
                        rowzero;
                rowzero = Highcharts.chart(elem.querySelector(".zeros"), {
                    chart: {
                        zoomType: 'xy'
                    },
                    title: { text: 'Row Zero Statistics' },
                    xAxis: {
                        title: { text: 'Number of Zero Counts' },
                        crosshair: true,
                        minRange: 0,
                        maxRange: data.length
                    },
                    yAxis: [{
                            title: { text: 'Count Metrics' },
                            type: 'logarithmic',
                            crosshair: true
                        },
                        {
                            title: { text: 'Fraction of Features' },
                            opposite: true,
                            crosshair: true
                        },
                        {
                            title: { text: 'Number of Features' },
                            opposite: true,
                            crosshair: true
                        }
                    ],
                    series: [
                        {
                            name: 'Mean',
                            data: data.map(function(x) {
                                return [x.num_zeros, x.mean]
                            }),
                            yAxis: 0
                        },
                        {
                            name: 'Nonzero Mean',
                            data: data.map(function(x) {
                                return [x.num_zeros, x.nonzero_mean]
                            }),
                            yAxis: 0
                        },
                        {
                            name: 'Median',
                            data: data.map(function(x) {
                                return [x.num_zeros, x.median]
                            }),
                            yAxis: 0
                        },
                        {
                            name: 'Nonzero Median',
                            data: data.map(function(x) {
                                return [x.num_zeros, x.nonzero_median]
                            }),
                            yAxis: 0
                        },
                        {
                            name: 'Fraction',
                            data: data.map(function(x) {
                                return [x.num_zeros, x.feature_frac]
                            }),
                            yAxis: 1
                        },
                        {
                            name: 'Cumulative Fraction',
                            data: data.map(function(x) {
                                return [x.num_zeros, x.cum_feature_frac]
                            }),
                            yAxis: 1
                        },
                        {
                            name: 'Number of Features',
                            data: data.map(function(x) {
                                return [x.num_zeros, x.num_features]
                            }),
                            yAxis: 2
                        },
                    ]
                });

                addFullscreenButton(
                    elem.querySelector("#rowzero-card-fullscreen"),
                    rowzero
                );


