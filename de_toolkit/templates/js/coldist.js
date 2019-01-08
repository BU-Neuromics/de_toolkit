var data = d.properties.dists;
                Highcharts.chart(elem.querySelector(".histogram"), {
                    chart: { },
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

                Highcharts.chart(elem.querySelector(".percentile"), {
                    chart: { },
                    title: { text: 'Counts Percentile Plot' },
                    series: data.map(
                            function(x,i) {
                                return {
                                    name: x.name,
                                    data: x.percentiles
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


