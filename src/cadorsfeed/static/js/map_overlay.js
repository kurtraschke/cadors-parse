google.load("earth", "1");
google.setOnLoadCallback(function () {
    $(document).ready(function () {
        $('div.report').each(
            function (index, element) {
                var thelink, thekml, theoverlay;
                thelink = $('a.maplink', element);
                thekml = thelink.attr('href');
                theoverlay = $('div.overlay', element);
 
                $(thelink).overlay({
                    top: 'center',
                    target: $(theoverlay),
                    onLoad: function (event) {
                        var initCB, failureCB, themap;
                        initCB = function (instance) {
                            var ge, link, href, networkLink;
                            ge = instance;
                            ge.getWindow().setVisibility(true);
                            ge.getNavigationControl().setVisibility(
                                ge.VISIBILITY_AUTO);
                            ge.getLayerRoot().enableLayerById(ge.LAYER_BORDERS,
                                                              true);
                            ge.getOptions().setStatusBarVisibility(true);
                            ge.getOptions().setScaleLegendVisibility(true);
            
                            link = ge.createLink('');
                            href = thekml;
                            link.setHref(href);
 
                            networkLink = ge.createNetworkLink('');
                            networkLink.set(link, true, true);
 
                            ge.getFeatures().appendChild(networkLink);
                        };
 
                        failureCB = function (errorCode) {
                            console.log(errorCode);
                        };

                        themap = $('div.map', theoverlay)[0];

                        google.earth.createInstance(themap, initCB, failureCB);
	                },

                    onClose: function (event) {
                        //Clear out the overlay so the plugin goes away.
                        $('div.map', theoverlay)[0].innerHTML = '';
                    }
                });
            }
        );
    });
});
