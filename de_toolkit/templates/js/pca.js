var data = d.properties.components.slice(0,10),
                        parallel,
                        parallel_elem = elem.querySelector(".parallel"),
                        parallel_controls,
                        pairwise,
                        update_parallel_series;

                    // component projection parallel coordinate plot
                    parallel_controls = parallel_elem.parentNode.querySelector(".controls");

                    // augment column data with viz aesthetics
                    addColumnDataAesthetics(
                        parallel_controls,
                        d.properties.column_variables
                    );

                    update_parallel_series = function(color_by) {
                        return d.properties.column_names.map(
                            function(x,i) {
                                var column = _.findWhere(
                                        d.properties.column_variables.columns,
                                        {column:color_by}
                                    ),
                                    color,
                                    dashStyle;
                                if(column !== undefined) {
                                    color = column.colors[i];
                                    dashStyle = column.dashStyles[i];
                                }
                                return {
                                    name: x,
                                    color: color,
                                    dashStyle: dashStyle,
                                    data: data.map(
                                        function(y) {
                                            return y.projections[i];
                                        }
                                    )
                                }
                            }
                        )
                    }

                    parallel = Highcharts.chart(parallel_elem, {
                        chart: {
                            parallelCoordinates: true 
                        },
                        title: { text: 'PCA Projections' },
                        tooltip: {
                            formatter: function() {
                                var tip = ['<strong>'+this.series.name+'</strong>'],
                                    column_i = d.properties.column_variables.sample_names.indexOf(this.series.name);
                                d.properties.column_variables.columns.map(
                                    function(column) {
                                        tip.push('<strong>'+column.column+':</strong> '+column.values[column_i]);
                                    }
                                );
                                return tip.join('<br/>');
                            }
                        
                        },
                        xAxis: {
                            categories: _.map(data,
                                function(x) {
                                    return x.name + ' (' + (x.perc_variance*100).toFixed(2) + '%)';
                                }
                            ),
                            labels: { styles: { color: '#DFDFDF' } }
                        },
                        plotOptions: {
                            series: {
                                animation: true,
                                marker: {
                                    enabled: false
                                },
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
                        series: update_parallel_series()
                    });
                    addFullscreenButton(
                        elem.querySelector("#parallel-card-fullscreen"),
                        parallel
                    );

                    // insert aesthetic options if column data exists
                    if(d.properties.column_variables.columns.length > 0) {
                        var select_elem = parallel_controls.querySelector("#color_by");
                        select_elem.onchange = function() {
                            var val = this.options[this.selectedIndex].value;
                            _.map(parallel.series,
                                function(series) {
                                    var column = _.findWhere(
                                            d.properties.column_variables.columns,
                                            {column:val}
                                        ),
                                        column_i = d.properties.column_variables.sample_names.indexOf(series.name),
                                        lineColor,
                                        dashStyle;
                                    if(column !== undefined) {
                                        lineColor = column.lineColor[column_i];
                                        dashStyle = column.dashStyles[column_i];
                                    }
                                    series.update({
                                            color: lineColor,
                                            dashStyle: dashStyle
                                        },
                                        redraw=false
                                    );
                                }
                            );
                            parallel.redraw();
                        }
                        d.properties.column_variables.columns.map(
                            function(column) {
                                var node = document.createElement('option');
                                node.setAttribute("value",column.column);
                                node.innerHTML = column.column;
                                select_elem.append(node);
                            }
                        );
                    }

                    /* pairwise component plot */
                    var pairwise_component_series = function(
                        i,
                        j,
                        color_by,
                        shape_by,
                        size_by
                    ) {
                        var series = [];
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
                                        var lineColor, fillColor, symbol, radius,
                                            column_i = d.properties.column_variables.sample_names.indexOf(sxy[0]);

                                        function get_col_value(col,value) {
                                            var column = _.findWhere(
                                                d.properties.column_variables.columns,
                                                {column:col}
                                            );
                                            return (column !== undefined ? column[value][column_i] : undefined);
                                        }

                                        // color
                                        lineColor = get_col_value(color_by,'lineColor');
                                        lineWidth = get_col_value(color_by,'lineWidth');
                                        fillColor = get_col_value(color_by,'fillColor');

                                        // shape
                                        symbol = get_col_value(shape_by,'symbol');

                                        // size
                                        radius = get_col_value(size_by,'radius');

                                        return {
                                            name: sxy[0],
                                            x: sxy[1],
                                            y: sxy[2],
                                            marker: {
                                                fillColor: fillColor,
                                                lineColor: lineColor,
                                                lineWidth: lineWidth,
                                                symbol: symbol,
                                                radius: radius
                                            }
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
                                        var lineColor, fillColor, symbol, radius,
                                            column_i = d.properties.column_variables.sample_names.indexOf(sxy[0]);

                                        function get_col_value(col,value) {
                                            var column = _.findWhere(
                                                d.properties.column_variables.columns,
                                                {column:col}
                                            );
                                            return (column !== undefined ? column[value][column_i] : undefined);
                                        }

                                        // color
                                        lineColor = get_col_value(color_by,'lineColor');
                                        fillColor = get_col_value(color_by,'fillColor');

                                        return {
                                            name: sxy[0],
                                            y: sxy[1],
                                            color: lineColor
                                        }
                                    }
                                )
                            }];
                        }
                        return series;
                    };
                    var pcs = _.pluck(data,'name'),
                        pairwise_elem = elem.querySelector(".pca_pairwise");

                    pairwise = Highcharts.chart(pairwise_elem,{
                        chart: { },
                        tooltip: {
                            formatter: function() {
                                var tip = ['<strong>'+this.key+'</strong>'],
                                    column_i = d.properties.column_variables.sample_names.indexOf(this.key);
                                d.properties.column_variables.columns.map(
                                    function(column) {
                                        tip.push('<strong>'+column.column+':</strong> '+column.values[column_i]);
                                    }
                                );
                                return tip.join('<br/>');
                            }

                        },
                        title: { text: 'Pairwise Component Plot' },
                        legend: { enabled: false },
                        xAxis: {
                            title: {
                                text: d.properties.components[1].name + ' (' + (d.properties.components[1].perc_variance*100).toFixed(2) + '% var.)'
                            }
                        },
                        yAxis: {
                            title: {
                                text: d.properties.components[0].name + ' (' + (d.properties.components[0].perc_variance*100).toFixed(2) + '% var.)'
                            }
                        },
                        series: pairwise_component_series(0,1)
                    });
                    var pairwise_controls = pairwise_elem.parentNode.querySelector(".controls"),
                        updateComponents;

                    updateComponents = function() {
                        var pc1 = $(pairwise_controls).find(".pc1_slider"),
                            pc2 = $(pairwise_controls).find(".pc2_slider"),
                            color_by = pairwise_controls.querySelector("#color_by"),
                            shape_by = pairwise_controls.querySelector("#shape_by"),
                            size_by = pairwise_controls.querySelector("#size_by"),
                            series,
                            i,j,
                            comp_i, comp_j;

                        i = pc1.slider("option","value");
                        j = pc2.slider("option","value");

                        // update the x and y axis titles
                        comp_i = d.properties.components[i];
                        pairwise.xAxis[0].setTitle({
                            text: comp_i.name + ' (' + (comp_i.perc_variance*100).toFixed(2) + '% var.)'
                        });
                        if(i != j) {
                            comp_j = d.properties.components[j];
                            pairwise.xAxis[0].setCategories(null);
                            pairwise.yAxis[0].setTitle({
                                text: comp_j.name + ' (' + (comp_j.perc_variance*100).toFixed(2) + '% var.)'
                            });
                        } else {
                            pairwise.xAxis[0].setCategories(d.properties.column_names);
                            pairwise.yAxis[0].setTitle({text: 'Sample'});
                        }

                        series = pairwise_component_series(
                            i, j,
                            color_by.options[color_by.selectedIndex].value,
                            shape_by.options[shape_by.selectedIndex].value,
                            size_by.options[size_by.selectedIndex].value
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
                    $(pairwise_controls).find(".pc1_slider").slider({
                        min:0,
                        value:0,
                        max:9,
                        change: updateComponents,
                    });
                    $(pairwise_controls).find(".pc2_slider").slider({
                        min:0,
                        value:1,
                        max:9,
                        change: updateComponents
                    });

                    addFullscreenButton(
                        elem.querySelector("#pairwise-card-fullscreen"),
                        pairwise
                    );

                    // insert aesthetic options if column data exists
                    if(d.properties.column_variables.columns.length > 0) {

                        var color_by = pairwise_controls.querySelector("#color_by"),
                            shape_by = pairwise_controls.querySelector("#shape_by"),
                            size_by = pairwise_controls.querySelector("#size_by");

                        color_by.onchange = updateComponents
                        shape_by.onchange = updateComponents
                        size_by.onchange = updateComponents

                        d.properties.column_variables.columns.map(
                            function(column) {
                                var node = document.createElement('option');
                                node.setAttribute("value",column.column);
                                node.innerHTML = column.column;
                                color_by.append(node);

                                if(column.type != 'continuous') {
                                    shape_by.append(node.cloneNode(true));
                                }
                                size_by.append(node.cloneNode(true));
                            }
                        );
                    }



