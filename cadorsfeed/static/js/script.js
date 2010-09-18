google.load("maps", "3.2", {other_params: "sensor=false"});
google.load("language", "1");
google.load("jquery", "1.4.2");
google.load("jqueryui", "1.8.4");

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
    //.substr(0,500)
    google.language.detect(content, detect_callback(tabs, index));
    //In the callback:
    function detect_callback(tabs, index) {
        return function(result) {
            if (!result.error){
                if (result.isReliable && result.language == 'en') {
                    //text is English
                    do_translate(tabs, index, 'en');
                } else if (result.isReliable && result.language == 'fr'){
                    //text is French
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

    content = $(rptid, tabs).html();

    google.language.translate(content, thislang, targetlang,
                              translate_callback(tabs, index, targetlangname));

    function translate_callback(tabs, index, targetlangname) {
        return function(result) {
            if (!result.error) {
                branding = document.createElement('div');
                google.language.getBranding(branding);
                trid = index+"-tr";
                tr = $("<div></div>").attr('id',trid);
                tr.append(result.translation);
                tr.append(branding);
                tabs.append(tr);
                tabs.tabs("add","#"+trid,targetlangname, 1);
            } else {
                add_error(tabs, index);
            }
        }
    }
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

    if (links.size() > 0) {

        tabid = index+'-map';
        containerid = index+'-mapcontainer';

        maptab = $('<div></div>').attr('id',tabid).append($('<div></div>').attr('id', containerid).attr('style','height: 300px; width: 800px;'));

        tabs.append(maptab);
        tabs.tabs("add","#"+tabid,"Map");

        bounds = new google.maps.LatLngBounds();
        markers = new Array();

        links.each(function(index) {
            coordinates = $(this).attr('title').split(', ');
            text = $(this).html()
            latlng = new google.maps.LatLng(coordinates[0], coordinates[1]);
            marker = new google.maps.Marker({
                position: latlng,
                title: text
            });
            bounds.extend(latlng);
            markers.push(marker);
        });

        center = bounds.getCenter();

        var options = {
            zoom: 8,
            center: bounds.getCenter(),
            mapTypeId: google.maps.MapTypeId.HYBRID
        };

        map = new google.maps.Map(document.getElementById(containerid), options);

        for (marker in markers) {
            markers[marker].setMap(map);
        }

        function tabcb(tabid, map, center) {
            return function(event, ui) {
                if (ui.panel.id == tabid) {
                    google.maps.event.trigger(map, 'resize');
                    map.panTo(center);
                }
            }
        }
        tabs.bind('tabsshow', tabcb(tabid, map, center));
    }
}

function initialize() {
    $(document).ready(function(){
        $('.hentry').each(function(index) {
            index = index + 1;
            elem = $('.entry-content', this);
            tabs = tabify(elem, index);
            detect(tabs, index);
            mapify(tabs, index);
        });
    });
}
google.setOnLoadCallback(initialize);