var bounds = {
                            mean_max: 0, mean_min: Number.MAX_SAFE_INTEGER,
                            median_max: 0, median_min: Number.MAX_SAFE_INTEGER
                        },
                        colzero;

                addFullscreenButton(
                    elem.querySelector("#rowzero-card-fullscreen"),
                    rowzero
                );

                d.properties.zeros.map(
                    function(x) {
                        bounds.mean_max = Math.max(x.mean, x.nonzero_mean, bounds.mean_max);
                        bounds.mean_min = Math.min(x.mean, x.nonzero_mean, bounds.mean_min);
                        bounds.median_max = Math.max(x.median, x.nonzero_median, bounds.median_max);
                        bounds.median_min = Math.min(x.median, x.nonzero_median, bounds.median_min);
                    }
                )
                colzero = Highcharts.chart(elem.querySelector(".parallel"), {
                    chart: { parallelCoordinates: true },
                    title: { text: 'Column Zeros' },
                    xAxis: {
                        categories: ['# Zero','Zero frac','Mean','Nonzero Mean', 'Median','Non-zero median'],
                        labels: {
                            styles: {
                                color: '#DFDFDF'
                            }
                        }
                    },
                    yAxis: [
                        {}, // # zero
                        {}, // # zero frac
                        {
                            max: bounds.mean_max,
                            min: bounds.mean_min
                        }, // mean
                        {
                            max: bounds.mean_max,
                            min: bounds.mean_min
                        }, // nonzero mean
                        {
                            max: bounds.median_max,
                            min: bounds.median_min
                        }, // median
                        {
                            max: bounds.median_max,
                            min: bounds.median_min
                        }, // nonzero median
                    ],
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
                    series: d.properties.zeros.map(
                        function(x,i) {
                            return {
                                name: x.name,
                                data: [
                                    x.zero_count, x.zero_frac,
                                    x.mean, x.nonzero_mean,
                                    x.median, x.nonzero_median
                                ]
                            }
                        }
                    )
                });

                addFullscreenButton(
                    elem.querySelector("#colzero-card-fullscreen"),
                    colzero
                );

