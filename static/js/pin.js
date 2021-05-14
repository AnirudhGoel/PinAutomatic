var cont = false;
var bookmark = null;
var t;
var done = 0;

$(document).ready(function() {
	updateSessionStatus();
	updateRequestsLeft();
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

	var pinLink = $("#pin_link").val() ? $("#pin_link").val() : null;
	var pinTitle = $("#pin_title").val() ? $("#pin_title").val() : null;
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
		if (data.code == 429) {
			$('#status').text(data.data);
			$("#pin-button").attr("disabled", false);
			return;
		}

		destinationBoard = data.destination  // This call also converts board name to board ID

		if (data.code == 200 && data.pins_copied != "") {
			cont = confirm("You have pinned " + data.pins_copied + " pins from this URL. Do you want to continue with the next one? Press Cancel to restart.");

			bookmark = data.pins_copied
		}

		$.ajax({
			type: 'POST',
			url: "pin-it",
			data: JSON.stringify({source: sourceURL, destination: destinationBoard, cont: cont, bookmark: bookmark, pin_link: pinLink, description: description, pin_title: pinTitle}),
			contentType: "application/json",
			dataType: 'json',
			success: function(result) {
				// console.log(result);
				if (result.code == 401) {
					window.location.href = result.data;
				} else if (result.code == 500) {
					$('#status').text('Unexpected error occurred: ' + result.data + ' Please contact the developer.');
					$("#pin-button").attr("disabled", false);
				} else if (result.code == 204) {
					$('#status').text(result.data);
					$("#pin-button").attr("disabled", false);
				} else if (result.code == 422) {
					$('#status').text(result.data);
					$("#pin-button").attr("disabled", false);
				} else {
					updateSessionStatus();
				}
			}
		});
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

function updateSessionStatus() {
	$.ajax({
		url: 'check-session-status',
		success: function(data) {
			// console.log(data);
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
				return;
			}
			t = setTimeout(updateSessionStatus, 2000);
		}
	});
}

function updateRequestsLeft() {
	$.get('get-requests-left', function (data) {
		$("#requests-left").text(data.pinterest_req_left);
		$("#pins-added").text(data.pins_added);

		p = setTimeout(updateRequestsLeft, 2000);
	});
}