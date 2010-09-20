google.load("maps", "3.2", {other_params: "sensor=false"});
google.load("language", "1");
google.load("jquery", "1.4.2");
google.load("jqueryui", "1.8.5");

function tabify(element, index) {
    id = index+"-report";
    tabs = $("<div></div>").attr('id',index+"-tabs");
    tabs.append($("<div></div>").attr('id',id).append(element.clone()));
    var list = $('<ul></ul>');
    list.append('<li><a href="#'+id+'">Report</a></li>');
    tabs.prepend(list);
    element.replaceWith(tabs);
    tabs.tabs();
    return tabs;
}

function detect(tabs, index) {
    //Get the report div, get its content
    id = index+"-report";
    content = $('#'+id,tabs).html()
    //Perform the detection
    google.language.detect(content.substr(0,500), detect_callback(tabs, index));
    //In the callback:
    function detect_callback(tabs, index) {
        return function(result) {
            if (!result.error){
                if (result.isReliable && result.language == 'en') {
                    do_translate(tabs, index, 'en');
                } else if (result.isReliable && result.language == 'fr'){
                    do_translate(tabs, index, 'fr');
                } else {
                    //detection was not reliable or language was neither en nor fr
                    add_notice(tabs, index);
                }
            } else {
                add_error(tabs, index);
            }
        }
    }
}

function do_translate(tabs, index, thislang) {
    targetlang = (thislang == 'en') ? 'fr' : 'en';
    thislangname = (thislang == 'en') ? 'English' : 'Français';
    targetlangname = (targetlang == 'en') ? 'English' : 'Français';
    //Set the tab title
    rptid = "#"+index+"-report";
    $("a[href='"+rptid+"']", tabs).html(thislangname);

    trid = index+"-tr";
    content = $(rptid, tabs).clone().attr('id',trid);
    translate_p(content, thislang, targetlang);
    branding = document.createElement('div');
    google.language.getBranding(branding);
    content.append(branding);
    tabs.append(content);
    tabs.tabs("add","#"+trid,targetlangname, 1);
}

function translate_p(content_div, source, target) {
    $("p", content_div).each(function(index) {
        p_content = $(this);
        function cb(p_content) {
            return function(result) {
                if (!result.error) {
                    new_content = $("<p>").append(result.translation);
                    p_content.replaceWith(new_content);
                    //FIXME: copy link handlers over.
                } //TODO: error handling
            }
        }
        google.language.translate(p_content.html(), source, target, cb(p_content))
    });
}

function add_error(tabs, index) {
    alert("error");
    rptid = "#"+index+"-report";
    msg = $('<div class="ui-widget"><div class="ui-state-error ui-corner-all" style="margin-top: 20px; padding: 0 .7em;"><p><span class="ui-icon ui-icon-alert" style="float: left; margin-right: .3em;"></span>There was a translation error.</p></div></div>');
    $(rptid, tabs).prepend(msg);
}

function add_notice(tabs, index) {
    //We don't know the content language.  Add a panel with buttons and let the user tell us.
    rptid = "#"+index+"-report";

    msg = $('<div class="ui-widget"><div class="ui-state-highlight ui-corner-all" style="margin-top: 20px; padding: 0 .7em;"><p><span class="ui-icon ui-icon-info" style="float: left; margin-top: .6em; margin-right: .3em;"></span>We could not determine the language of this report. Please select the language of this report:&nbsp;</p></div></div>');

    function callback(msg, tabs, index, thislang) {
        return function() {
            msg.hide();
            msg.remove();
            do_translate(tabs, index, thislang);
        }
    }
    en = $('<button>English</button>').button().click(callback(msg, tabs, index, 'en'));
    fr = $('<button>Français</button>').button().click(callback(msg, tabs, index, 'fr'));
    $('p', msg).append(en).append("&nbsp;").append(fr);
    $(rptid, tabs).prepend(msg);
}


function mapify(tabs, index) {
    rptid = "#"+index+"-report";
    content = $(rptid, tabs)

    links = $('a[class=\'geolink\']', content);
    //Only add a map tab if there is at least one map link.
    if (links.size() > 0) {

        tabid = index+'-map';
        containerid = index+'-mapcontainer';

        maptab = $('<div></div>').attr('id',tabid).append($('<div></div>').attr('id', containerid).attr('style','height: 400px; width: 100%;'));

        tabs.append(maptab);
        tabs.tabs("add","#"+tabid,"Map");

        bounds = new google.maps.LatLngBounds();
        markers = new Array();

        var options = {
            zoom: 8,
            center: new google.maps.LatLng(0,0),
            mapTypeId: google.maps.MapTypeId.HYBRID,
            scrollwheel: false,
        };

        map = new google.maps.Map(document.getElementById(containerid), options);

        links.each(function(index) {
            coordinates = $(this).attr('title').split(', ');
            text = $(this).html()
            latlng = new google.maps.LatLng(coordinates[0], coordinates[1]);
            marker = new google.maps.Marker({
                position: latlng,
                title: text,
                map: map
            });
            bounds.extend(latlng);
            markers.push(marker);

            function click_cb(map, latlng, tabs, tabid) {
                return function(event) {
                    event.preventDefault();
                    tabs.tabs("select","#"+tabid);
                    map.panTo(latlng);
                    map.setZoom(map.getZoom() + 2);
                }
            }

            $(this).click(click_cb(map, latlng, tabs, tabid));
        });

        function tabcb(tabid, map, bounds) {
            return function(event, ui) {
                if (ui.panel.id == tabid) {
                    google.maps.event.trigger(map, 'resize');
                    map.fitBounds(bounds);
                    map.setZoom(map.getZoom()-2);
                }
            }
        }
        tabs.bind('tabsshow', tabcb(tabid, map, bounds));
    }
}

function initialize() {
    $(document).ready(function(){
        $('.hentry').each(function(index) {
            index = index + 1;
            elem = $('.entry-content', this);
            tabs = tabify(elem, index);
        });
        $('.hentry').each(function(index) {
            index = index + 1;
            tabs = $("#"+index+"-tabs", this);
            detect(tabs, index);
            mapify(tabs, index);
        });
    });
}

google.setOnLoadCallback(initialize);