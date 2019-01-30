// report gen code
            function addFullscreenButton(elem,chart) {
                var origHeight = chart.chartHeight;
                $(elem).click(function() {
                    var card = $(this).closest('.card');
                    card.toggleClass('card-fullscreen');
                    if(card.hasClass('card-fullscreen')) {
                        chart.setSize(null,null);
                    } else {
                        chart.setSize(null, origHeight);
                        chart.reflow();
                    }
                });
            }

            function allNumericOrNaN(l) {
                return _.every(l,
                    function(x) {
                        return isNaN(x) || !isNaN(parseFloat(x)) && !isNaN(x - 0);
                    }
                )
            }

            var custom_shapes = {
                cross: function (x, y, w, h) {
                        return ['M', x, y, 'L', x + w, y + h, 'M', x + w, y, 'L', x, y + h, 'z'];
                },
                empty_circle: function(x,y,w,h) {

                }
            };

            _.mapObject(custom_shapes,
                function(fn,name) {
                    Highcharts.SVGRenderer.prototype.symbols[name] = fn
                    if (Highcharts.VMLRenderer) {
                        Highcharts.VMLRenderer.prototype.symbols[name] = Highcharts.SVGRenderer.prototype.symbols[name];
                    }
            });

            var colors, shapes;

            // default Highcharts 3.x colors
            colors = ['#2f7ed8', '#0d233a', '#8bbc21', '#910000', '#1aadce',
                      '#492970', '#f28f43', '#77a1e5', '#c42525', '#a6c96a'];

            colors = colors.map(function(x) {
                var c = d3.color(x);
                c.opacity = 0.5;
                return c.toString();
            });
            shapes = ['circle','square','diamond','triangle','triangle-down'];

            function takeN(l,n) {
                var i = 0,
                    arr = Array();
                while(arr.length<n) {
                    arr.push(l[i]);
                    i = (i+1)%l.length;
                }
                return arr;
            }
            /* the callback should be a function that accepts a single array
               containing elements like:
                {
                    'name': 'sample name',
                    'columns': [
                        {
                            'column': 'status',
                            'style': {
                                'color': '#600',
                                'shape': 'rectangle',
                                'size': 100
                            }
                        },
                        {
                            'column': 'AgeOfOnset',
                            'style': {
                                'color': '#531',
                                'shape': null,
                                'size': 120
                            }
                        }
                    ]
                }
                the callback should handle updating whatever plot with the
                style as appropriate
            */
            function addColumnDataAesthetics(elem,column_data,callback) {
                // identify the different column data column types
                // a column will be considered categorical if:
                //   - there are any values in the column that can't be parsed
                //     as numeric
                //   - all values can be parsed as numeric, but the number of
                //     unique values is less than or equal to 20% of the number
                //     of values in the array
                // this augments column_data.columns to have a type field

                _.map(column_data.columns,
                    function(column, i) {
                        var unique,
                            num_vals = column.values.length;
                        column.type = 'categorical';
                        if(allNumericOrNaN(column.values)) {
                            unique = _.uniq(column.values);
                            if(unique.length/num_vals > 0.2) {
                                column.type = 'continuous';
                            }
                        }
                    }
                );

                _.map(column_data.columns,
                    function(column, i) {
                        var style_map;
                        if(column.type == 'categorical') {
                            var unique,
                                val_map;
                            unique = _.uniq(column.values);

                            val_map = d3.scaleOrdinal()
                                .domain(unique);

                            column.lineColor = column.values.map(
                                val_map.range(takeN(colors,unique.length))
                                       .unknown('rgb(128,128,128,0.5)')
                            );

                            column.fillColor = column.values.map(
                                val_map.range(takeN(colors,unique.length))
                                       .unknown('none')
                            );

                            column.symbol = column.values.map(
                                val_map.range(takeN(shapes,unique.length))
                                       .unknown('cross')
                            );

                            column.radius = column.values.map(
                                val_map.range([2,6]).unknown(2)
                            );

                        } else {
                            var no_nan, val_map, base_color, color_map, size_map;
                            no_nan = _.filter(column.values,function(x) { return !isNaN(x) });

                            val_map = d3.scaleLinear()
                                .domain(
                                    [
                                        Math.min(...no_nan),
                                        Math.max(...no_nan)
                                    ]);

                            base_color = d3.color(colors[i%colors.length]);

                            column.lineColor = column.values.map(
                                val_map.range([
                                    base_color.brighter(5),
                                    base_color
                                ]).unknown('rgb(128,128,128,0.5)')
                            );

                            column.fillColor = column.values.map(
                                val_map.range([
                                    base_color.brighter(5),
                                    base_color
                                ]).unknown('none')
                            );

                            column.symbol = null;

                            column.radius = column.values.map(
                                val_map.range([4,10]).unknown(4)
                            );

                        }

                        column.lineWidth = column.values.map(
                            function(x) {
                                if(_.isNaN(x)) {
                                    return 1;
                                }
                                return 0;
                            }
                        );

                        column.dashStyles = column.values.map(
                            function(x) {
                                if(_.isNaN(x)) {
                                    return 'Dash';
                                }
                                return 'Solid';
                            }
                        );

                    }
                )

            }


            $(document).ready(function() {

                // load templates
                detk.templates = {};
                document.querySelectorAll("template").forEach(function(elem, i) {
                        detk.templates[elem.id] = doT.template(elem.innerHTML);
                    }
                );

                // create a module for each input file
                _.mapObject(
                    _.groupBy(detk.data,'in_file_path'),
                        function(mods, fn) {
                            var id = 'div_'+fn.replace('.','_');
                            var node = document.createElement('div');
                            node.innerHTML = detk.templates["file_div"]({"id":id,"name":fn});
                            document.getElementById("modules").appendChild(node);

                            mods = _.sortBy(mods,'name');

                            mods.forEach(function(d) {
                                

                                // populate the 'body' value with the template
                                if(detk.templates.hasOwnProperty(d.name)) {
                                    d.body = detk.templates[d.name](d);
                                    var node = document.createElement('div');
                                    node.innerHTML = detk.templates.file_section(d);
                                    document.getElementById(id).appendChild(node);
                                }

                                // call the javascript function by type
                                if(detk.functions.hasOwnProperty(d.name)) {
                                    detk.functions[d.name](
                                        document.getElementById("body_"+d.id),
                                        d
                                    );
                                }
                            });
                        }
                );

                // remove the blinds
                $("#blind").addClass("invisible");
                $(".loader").css("animation","none");

            });

