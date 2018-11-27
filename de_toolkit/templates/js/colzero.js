                var container = $("#"+elem+" > #colzero_count")[0];
                Highcharts.chart(container.id, {
                    chart: { type: 'column' },
                    title: { text: 'colzero' },
                    xAxis: { title: { text: 'Sample' }, },
                    yAxis: { title: { text: '# zeros' } },
                    series: [{
                        name: 'Zero counts',
                        data: _.map(
                            _.sortBy(d.properties.zeros,'zero_count'),
                                function(x) {
                                    return {
                                        name: x.name,
                                        color: '#00FF00',
                                        y: x.zero_count
                                    }
                            })
                    }]
                });

