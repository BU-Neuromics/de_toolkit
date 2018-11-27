var data = _.sortBy(d.properties.entropies,'entropy');
                data.reverse();
                Highcharts.chart(elem.find(".entropy")[0], {
                    title: { text: 'Sample Entropy' },
                    xAxis: {
                        title: { text: 'Features' },
                        categories: _.pluck(data,'name')
                    },
                    series: [{
                        name: 'Sample Entropy',
                        data: _.pluck(data,'entropy'),
                        
                    }]
                });


