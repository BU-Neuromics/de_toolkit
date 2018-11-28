// component projection parallel coordinate plot
                var data = d.properties.components.slice(0,10);
                Highcharts.chart(elem.find(".pca_parallel")[0], {
                    chart: { parallelCoordinates: true },
                    title: { text: 'PCA Projections' },
                    xAxis: {
                        categories: _.map(data,
                            function(x) {
                                return x.name + '(' + (x.perc_variance*100).toFixed(2) + '%)';
                            }
                        ),
                        labels: { styles: { color: '#DFDFDF' } }
                    },
                    plotOptions: {
                        series: {
                            animation: false,
                            states: {
                                hover: {
                                    halo: {
                                        size: 0
                                    }
                                }
                            },
                            events: {
                                mouseOver: function() {
                                    this.group.toFront();
                                }
                            }
                        }
                    },
                    colors: ['rgba(11, 200, 200, 0.3)'],
                    series: d.properties.column_names.map(
                        function(x,i) {
                            return {
                                name: x,
                                data: data.map(
                                    function(y) {
                                        return y.projections[i];
                                    }
                                )
                            }
                        }
                    )
                });

                var pcs = _.pluck(data,'name');
                Highcharts.chart(elem.find(".component_grid")[0], {
                    chart: {
                        type: 'heatmap',
                        marginTop: 15
                    },
                    title: { text: 'Pairwise Comparison' },
                    plotOptions: {
                        series: { }
                    },
                    tooltip: {
                        formatter: function() {
                            return pcs[this.point.x] + ' vs ' + pcs[this.point.y];
                        }
                    },
                    series: [{
                        name: 'Comparisons',
                        data: _.flatten(
                            pcs.map(function(pc1,i) {
                                return pcs.map(function(pc2,j) {
                                    return [i, j, 0];
                                })
                            }),
                            shallow=true
                        )
                    }]
                });
