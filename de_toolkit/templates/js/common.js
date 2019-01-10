// report gen code
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

