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
                    console.log(i,j);
                    
                    if (i != j) {
                        series = [{
                            name: 'PC'+(i+1)+' vs PC'+(j+1),
                            type: 'scatter',
                            data: _.map(
                                _.zip(
                                    d.properties.column_names,
                                    data[i].projections,data[j].projections
                                ),
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
                var controls = elem.querySelector(".controls"),
                    updateComponents;

                updateComponents = function() {
                    var pc1 = $(controls).find(".pc1_slider"),
                        pc2 = $(controls).find(".pc2_slider"),
                        series;
                    series = pairwise_component_series(
                        pc1.slider("option","value"),
                        pc2.slider("option","value")
                    );
                    pairwise.update({
                        title: { text: series[0].name },
                        series: series
                    });
                    pc1.find(".handle").text(pc1.slider("value")+1);
                    pc2.find(".handle").text(pc2.slider("value")+1);
                }

                    var updateSlider = function() {
                        };
                    $(controls).find(".pc1_slider").slider({
                        min:0,
                        value:0,
                        max:9,
                        change: updateComponents,
                    });
                    $(controls).find(".pc2_slider").slider({
                        min:0,
                        value:1,
                        max:9,
                        change: updateComponents
                    });

