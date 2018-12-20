// component projection parallel coordinate plot
                var data = d.properties.components.slice(0,10);
                Highcharts.chart(elem.querySelector(".parallel"), {
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

                var pairwise_component_series = function(i,j) {
                    var series = [];
                    
                    if (i != j) {
                        series = [{
                            name: 'PC'+(i+1)+' vs PC'+(j+1),
                            type: 'scatter',
                            data: _.map(
                                _.zip(d.properties.column_names, data[i].projections,data[j].projections),
                                function(sxy) {
                                    return {
                                        name: sxy[0],
                                        x: sxy[1],
                                        y: sxy[2],
                                    }
                                }
                            )
                        }];
                    } else {
                        series = [{
                            name: 'PC'+(i+1),
                            type: 'column',
                            data: _.map(
                                _.zip(d.properties.column_names, data[i].projections),
                                function(sxy) {
                                    return {
                                        name: sxy[0],
                                        y: sxy[1],
                                    }
                                }
                            )
                        }];
                    }
                    return series;
                };
                var pcs = _.pluck(data,'name');
                var pairwise = Highcharts.chart(elem.querySelector(".pca_pairwise"),{
                    chart: { },
                    series: pairwise_component_series(0,1)
                });
                Highcharts.chart(elem.querySelector(".component_grid"), {
                    chart: {
                        type: 'heatmap',
                        marginTop: 15
                    },
                    xAxis: { visible: false },
                    yAxis: { visible: false },
                    legend: { enabled: false },
                    title: { text: 'Compare PCs', fontsize: 9 },
                    plotOptions: {
                        series: { }
                    },
                    tooltip: {
                        formatter: function() {
                            if(this.point.x == this.point.y) {
                                return pcs[this.point.x];
                            } else {
                                return pcs[this.point.x] + ' vs ' + pcs[this.point.y];
                            }
                        }
                    },
                    series: [{
                        name: 'Comparisons',
                        label: { enabled: false },
                        pointPadding: 1,
                        events: {
                            click: function(event) {
                                //pairwise.series[0].setData([0].data);
                                var series = pairwise_component_series(event.point.x,event.point.y);
                                pairwise.update({
                                    title: { text: series[0].name },
                                    series: series
                                });
                            }
                        },
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
