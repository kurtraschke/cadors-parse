$(document).ready(function () {
    function set_location(position) {
        var latitude, longitude;
        latitude = position.coords.latitude;
        longitude = position.coords.longitude;
        $('#latitude').val(latitude);
        $('#longitude').val(longitude);
    }

    function location_error(error) {
        if (error.code === 1) {
            window.alert('You did not give permission for your location to be used.');
        } else {
            window.alert('Could not determine your location.');
        }
    }

    function get_location() {
        if (Modernizr.geolocation) {
            navigator.geolocation.getCurrentPosition(set_location, location_error);
        } else {
            window.alert('Your browser does not support geolocation.');
        }
    }

    $('#geolocate').click(get_location);
});
