var requestsLeft = 0;
var cont = false;
var cursor = false;
var bookmark = null;
var t;
var done = 0;

$(document).ready(function() {
	getRequestsLeft();
	updater();
});

function pinThem(event) {
	event.preventDefault();
	$("#pin-button").attr("disabled", true);

	done = 0;
	var err1 = $("#err1");
	var err2 = $("#err2");

	// var sourceBoard = extractBoard($("#source_board").val());
	var sourceURL = isValidUrl($("#source_url").val().trim());
	var destinationBoard = $("#destination_board").val().trim();

	var pinLink = $("#pin_link").val() ? $("#pin_link").val() != false : null;
	var description = $("#description").val() ? $("#description").val() : null;

	if (sourceURL == false) {
		err1.html("Enter a valid source URL");
		$("#pin-button").attr("disabled", false);
		return;
	} else if (destinationBoard == false) {
		err2.html("Enter a valid destination board");
		$("#pin-button").attr("disabled", false);
		return;
	}

	$.post('check-last-pin-status', {source: sourceURL, destination: destinationBoard},function (data) {
		console.log(data);
		if (data.code == 200 && data.pins_copied != "") {
			cont = confirm("You have pinned " + data.pins_copied + " pins from this URL. Do you want to continue with the next one? Press Cancel to restart.");

			console.log(cont);

			bookmark = data.pins_copied
		}

		$.post("pin-it", {source: sourceURL, destination: destinationBoard, requests_left: requestsLeft, cont: cont, bookmark: bookmark, pin_link: pinLink, description: description}, function(result) {
			console.log(result);
			if (result.code == 401) {
				window.location.href = result.data;
			} else if (result.code == 500) {
				$('#status').text('Unexpected error occurred: ' + result.data + 'Please contact the developer.');
			} else if (result.code == 204) {
				$('#status').text(result.data);
			} else if (result.code == 422) {
				$('#status').text(result.data);
			} else {
				updater();
			}
			$("#pin-button").attr("disabled", false);
		});
	});
}

function getRequestsLeft() {
	$.get('get-requests-left', function (data) {
		if (data.code == 401) {
			window.location.href = data.data;
		} else if (data.code == 200) {
			requestsLeft = data.data;
			console.log(requestsLeft);

			$("#pins-left").text(requestsLeft);
		}
	});
}

function isValidUrl(url) {
	var expression = /[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)?/gi;
	var regex = new RegExp(expression);

	if (url.match(regex)) {
		return url
	} else {
		return false
	}
}

function updater() {
	$.ajax({
		url: 'check-session-status',
		success: function(data) {
			console.log(data);
			status = data.status;
			$('#status').text(status);
			if (data.code == 200 || data.code == 404 || data.code == 500) {
				done = 1;
				$("#pin-button").attr("disabled", false);
			}
		},
		complete: function() {
			// Schedule the next request when the current one's complete
			if (done == 1) {
				clearTimeout(t);
				console.log("Clear Timeout");
				getRequestsLeft();
				return;
			}

			t = setTimeout(updater, 4000);
		}
	});
}