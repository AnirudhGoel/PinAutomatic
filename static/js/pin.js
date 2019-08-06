function pinThem(event) {
	event.preventDefault();
	$("#err1").html("");
	$("#err2").html("");

	var token = getCookie("pa-token");
	if (token == "") {
		$("body").html("<center><br><br><br><br><br><br><br><h1>Cookie Deleted !<br> Please login again.</h1></center>");
		setTimeout( function() {
			window.location = "https://pinterestautomatic.herokuapp.com/index.html"
		}, 2 * 1000 );
	}
	var source_board = $("#source_board").val();
	var destination_board = $("#destination_board").val();
	var error = 0;

	if (source_board.substring(0,6) == "https:") {
		var source_board_parts = source_board.split("/");
		var source_board = source_board_parts[3] + "/" + source_board_parts[4];
	} else if (source_board.replace(/^\/|\/$/g, "").split("/").length == 2) {
		source_board = source_board.replace(/^\/|\/$/g, "");
	} else {
		$("#err1").html("Enter a valid source board");
		error = 1;
	}

	if (destination_board.substring(0,6) == "https:") {
		var destination_board_parts = destination_board.split("/");
		var destination_board = destination_board_parts[3] + "/" + destination_board_parts[4];
	} else if (destination_board.replace(/^\/|\/$/g, "").split("/").length == 2) {
		destination_board = destination_board.replace(/^\/|\/$/g, "");
	} else {
		$("#err2").html("Enter a valid destination board");
		error = 1;
	}

	if (error == 0) {
		$("#response").html("<h1>Pinning...</h1>");
		$.get("https://pinterestautomatic.herokuapp.com/pin.php", {token: token, source_board: source_board,destination_board: destination_board}, function(result) {
			console.log(result);
			var result = JSON.parse(result);
			if (result.code == 0) {
				$("#response").html("<h1>Technical Error<br>Please try again later</h1>");
			} else if (result.code == 1) {
				$("#response").html("<h1>Error in adding pins...<br> Please check the details filled</h1>");
			} else if (result.code == 2) {
				$("#response").html("<h1>Pins added successfully !</h1>");
			}
		});
	}
}
function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length,c.length);
        }
    }
    return "";
}
function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    var expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + "; " + expires;
}