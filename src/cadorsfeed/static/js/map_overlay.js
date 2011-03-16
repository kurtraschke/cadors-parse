google.load("earth", "1");
google.setOnLoadCallback(function() {
$(document).ready(function() {
  

  $('div.report').each(
    function(index, element) {

      var thelink = $('a.maplink', element);
      var thekml = thelink.attr('href');
      var theoverlay = $('div.overlay', element);
 
      $(thelink).overlay({
        target: $(theoverlay),

        onLoad: function(event) {
          var initCB = function (instance) {
            var ge = instance;
            ge.getWindow().setVisibility(true);
            ge.getNavigationControl().setVisibility(ge.VISIBILITY_AUTO);

            var link = ge.createLink('');
            var href = thekml;
            link.setHref(href);
 
            var networkLink = ge.createNetworkLink('');
            networkLink.set(link, true, true);
 
            ge.getFeatures().appendChild(networkLink);
          }
 
          var failureCB = function(errorCode) {
            console.log(errorCode)
          }

          var themap = $('div.map', theoverlay)[0];

          google.earth.createInstance(themap,
            initCB, failureCB);
	},

        onClose: function(event) {
          //Clear out the overlay so the plugin goes away.
          $('div.map', theoverlay)[0].innerHTML = '';
        }

      });
    }
  );
})
});