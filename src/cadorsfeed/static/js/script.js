google.load("maps", "3.2", {other_params: "sensor=false"});
google.load("language", "1");

function jq(myid) {
   return '#' + myid.replace(/(:|\.)/g,'\\$1');
}

var tabconfig = {tabs: 'ul > li > a'};


function tabify(element) {
    var baseid = element.parent().attr('id');
    var reportid = baseid + "-report";
    var tabsid = baseid + "-tabs";
    var tabs = $('<div class="tabcontainer"></div>').attr('id', tabsid);
    var panes = $('<div class="panes"></div>');
    panes.append($('<div></div>').attr('id',reportid).append(element.clone()));
    var list = $('<ul class="tabs"></ul>');
    list.append('<li><a href="#'+reportid+'">Report</a></li>');
    tabs.append(list);
    tabs.append(panes);
    element.replaceWith(tabs);
    tabs.tabs("div.panes > div", tabconfig);
    return tabs;
}

function addtab(tabs, newcontent, tabtitle, suffix) {
    var baseid = tabs.parent().attr('id');
    $(".panes", tabs).append($('<div></div>').attr('id',baseid + suffix).append(newcontent));
    $(".tabs", tabs).append('<li><a href="#'+baseid + suffix+'">'+tabtitle+'</a></li>');
    tabs.tabs("div.panes > div", tabconfig);
    //Re-register the onClick callback if needed.
    var api = tabs.data('tabs');
    var callback = tabs.data('callback');
    if (callback) {
        api.onClick(callback);
    }
    
}

function detect(tabs) {
    //Get the report div, get its content
    var id = tabs.parent().attr('id')+"-report";
    var content = $(jq(id),tabs).html()
    //Perform the detection
    google.language.detect(content.substr(0,500), detect_callback(tabs));
    //In the callback:
    function detect_callback(tabs) {
        return function(result) {
            if (!result.error){
                if (result.isReliable && result.language == 'en') {
                    do_translate(tabs, 'en');
                } else if (result.isReliable && result.language == 'fr'){
                    do_translate(tabs, 'fr');
                } else {
                    //detection was not reliable or language was neither en nor fr
                    add_notice(tabs);
                }
            } else {
                add_error(tabs);
            }
        }
    }
}

function do_translate(tabs, thislang) {
    var targetlang = (thislang == 'en') ? 'fr' : 'en';
    var thislangname = (thislang == 'en') ? 'English' : 'Français';
    var targetlangname = (targetlang == 'en') ? 'English' : 'Français';
    //Set the tab title
    var rptid = tabs.parent().attr('id')+"-report";
    $("a[href='#"+rptid+"']", tabs).html(thislangname);

    var trid = tabs.parent().attr('id')+"-tr";
    var content = $(jq(rptid), tabs).clone().attr('id',trid);
    translate_p(content, thislang, targetlang);
    var branding = document.createElement('div');
    google.language.getBranding(branding);
    content.append(branding);

    addtab(tabs, content, targetlangname, "-tr");
}

function translate_p(content_div, source, target) {
    $("p", content_div).each(function() {
        var p_content = $(this);
        if (p_content.html().length <= 1000) {
            function cb(p_content) {
                return function(result) {
                    if (!result.error) {
                        var new_content = $("<p>").append(result.translation);
                        p_content.replaceWith(new_content);
                        //FIXME: copy link handlers over.
                    } //TODO: error handling
                }
            }
            google.language.translate(p_content.html(), source, target, cb(p_content))
        } else {
            //we should somehow tell the user the content was too long
        }
    });
}

function add_error(tabs) {
    var rptid =  tabs.parent().attr('id')+"-report";
    var msg = $('<div class="error"><p>There was a translation error.</p></div>');
    $(jq(rptid), tabs).prepend(msg);
}

function add_notice(tabs) {
    //We don't know the content language.  Add a panel with buttons and let the user tell us.
    var rptid =  tabs.parent().attr('id')+"-report";

    var msg = $('<div><p>We could not determine the language of this report. Please select the language of this report:&nbsp;</p></div>');

    function callback(msg, tabs, thislang) {
        return function() {
            msg.hide();
            msg.remove();
            do_translate(tabs, thislang);
        }
    }
    var en = $('<button>English</button>').click(callback(msg, tabs, 'en'));
    var fr = $('<button>Français</button>').click(callback(msg, tabs, 'fr'));
    $('p', msg).append(en).append(fr);
    $(jq(rptid), tabs).prepend(msg);
}


function addmaptab(tabs) {
    var tabid =  tabs.parent().attr('id')+'-map';
    var containerid = tabs.parent().attr('id')+'-mapcontainer';

    var maptab = $('<div></div>').attr('id',tabid).append($('<div></div>').attr('id', containerid).attr('style','height: 400px; width: 100%;'));

    addtab(tabs, maptab, "Map", "-map");

    var options = {
        zoom: 8,
        center: new google.maps.LatLng(0,0),
        mapTypeId: google.maps.MapTypeId.HYBRID,
        scrollwheel: false
    };

    var map = new google.maps.Map(document.getElementById(containerid), options);
    var bounds = new google.maps.LatLngBounds();
    bounds.count = 0;

    function tabcb(api, tabid, map, bounds) {
        return function(event, index) {
            if (!(('srcElement' in event) && ('hash' in event.srcElement))) {
                return;
            }
            if (event.srcElement.hash == '#'+tabid) {
                google.maps.event.trigger(map, 'resize');
                map.fitBounds(bounds);
                if (bounds.count > 1) {
                    map.setZoom(map.getZoom() - 2);
                } else {
                    map.setZoom(map.getZoom() - 4);
                }                               
            }
        }
    }

    var api = tabs.data('tabs');
    var callback = tabcb(api, tabid, map, bounds);
    tabs.data('callback', callback);
    api.onClick(callback);

    tabs.data('map', map);
    tabs.data('bounds', bounds);
}

function ensuremap(tabs) {
    if (tabs.data('map') == null) {
        addmaptab(tabs);
    }
}

function addpoint(map, bounds, latlng, text) {
    var marker = new google.maps.Marker({
        position: latlng,
        title: text,
        map: map
    });
    bounds.extend(latlng);
    bounds.count++;
}

function mapify(tabs) {
    var rptid =  tabs.parent().attr('id')+"-report";
    var content = $(jq(rptid), tabs)

    var links = $('a[class=\'geolink\']', content);
    var re = /(.*)\(((?:-)?\d{1,2}(?:\.\d{1,6})?), ?((?:-)?\d{1,3}(?:\.\d{1,6})?)\)$/

    //Only add a map tab if there is at least one map link.
    if (links.length) {
        var tabid = tabs.parent().attr('id')+'-map';
        ensuremap(tabs);
        var map = tabs.data('map');
        var bounds = tabs.data('bounds');

        links.each(function() {
            var coordinates = re.exec($(this).attr('title'));
            var text = coordinates[1]
            var latlng = new google.maps.LatLng(coordinates[2], coordinates[3]);

            addpoint(map, bounds, latlng, text);

            function click_cb(map, latlng, tabs, tabid) {
                return function(event) {
                    event.preventDefault();
                    var api = tabs.data('tabs');
                    api.click("#"+tabid);
                    google.maps.event.trigger(map, 'resize');
                    map.panTo(latlng);
                    map.setZoom(map.getZoom() + 2);
                }
            }

            $(this).click(click_cb(map, latlng, tabs, tabid));
        });
    }
}

function initialize() {
    $(document).ready(function(){
        $('.hentry').each(function() {
            var elem = $('.entry-content', this);
            var tabs = tabify(elem);
        });
        $('.hentry').each(function() {
            var id = $(this).attr('id')+"-tabs";
            var tabs = $(jq(id));
            detect(tabs);
            mapify(tabs);
        });
    });
}

google.setOnLoadCallback(initialize);