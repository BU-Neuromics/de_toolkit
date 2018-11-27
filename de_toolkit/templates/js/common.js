// report gen code
        $(document).ready(function() {

            // load templates
            detk.templates = {};
            $("template").each(function(id, elem) {
                    detk.templates[elem.id] = doT.template(elem.innerHTML);
                }
            );

            // create a module for each input file
            _.mapObject(
                _.groupBy(detk.data,'in_file_path'),
                    function(mods, fn) {
                        var id = 'div_'+fn.replace('.','_');
                        $("#modules").append(
                            detk.templates["file_div"](
                                {"id":id,"name":fn}
                            )
                        );
                        _.sortBy(mods,'name').forEach(function(d) {

                            // populate the 'body' value with the template
                            d.body = detk.templates[d.name](d);
                            $("#"+id).append(detk.templates.accordion(d));

                            // call the javascript function by type
                            if(d.name in detk.functions) {
                                detk.functions[d.name]($("#body_"+d.id),d);
                            }
                        });
                    }
            );

        });

