var data = d.properties.dists,
                        histogram,
                        percentile;
                histogram = Highcharts.chart(elem.querySelector(".histogram"), {
                    chart: {
                        events: {
                            click: function(e) {
                                if(this.xAxis[0].userOptions.type == 'linear') {
                                   this.xAxis[0].update({ type: 'logarithmic' });
                                   this.xAxis[0].userOptions.type == 'logarithmic';
                                } else {
                                   this.xAxis[0].update({ type: 'linear' });
                                   this.xAxis[0].userOptions.type == 'linear';
                                }
                            }
                        }
                    },
                    xAxis: {
                        title: { text: 'Counts' },
                        type: 'logarithmic'
                    },
                    yAxis: {
                        title: { text: '# of Features' },
                    },
                    legend: { enabled: false},
                    title: { text: 'Counts Distribution' },
                    series: data.map(
                            function(x,i) {
                                return {
                                    name: x.name,
                                    data: x.dist
                                }
                            }
                        ),
                    plotOptions: {
                        series: {
                            animation: true,
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
                    }

                });
                addFullscreenButton(
                    elem.querySelector("#histogram-card-fullscreen"),
                    histogram
                );

                percentile = Highcharts.chart(elem.querySelector(".percentile"), {
                    chart: {
                        events: {
                            click: function(e) {
                                if(this.xAxis[0].userOptions.type == 'linear') {
                                    this.xAxis[0].update({ type: 'logarithmic' });
                                    this.xAxis[0].userOptions.type == 'logarithmic';
                                } else {
                                    this.xAxis[0].update({ type: 'linear' });
                                    this.xAxis[0].userOptions.type == 'linear';
                                }
                            }
                        }
                    },
                    legend: { enabled: false},
                    xAxis: {
                        title: { text: 'Counts' },
                        type: 'logarithmic'
                    },
                    yAxis: {
                        title: { text: 'Percentile' },
                        type: 'linear'
                    },
                    title: { text: 'Counts Percentile Plot' },
                    series: data.map(
                            function(x,i) {
                                return {
                                    name: x.name,
                                    data: x.percentiles.map(function(x) {
                                        return [x[1], x[0]];
                                    })
                                }
                            }
                        ),
                    plotOptions: {
                        series: {
                            animation: true,
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
                    }

                });
                addFullscreenButton(
                    elem.querySelector("#percentile-card-fullscreen"),
                    percentile
                );


