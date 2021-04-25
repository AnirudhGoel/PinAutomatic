var requestsLeft = 0;
var cont = false;
var cursor = false;
var t;
var done = 0;

$(document).ready(function() {
	getRequestsLeft();
	updater();
});

function pinThem(event) {
	event.preventDefault();

	done = 0;

	var err1 = $("#err1");
	var err2 = $("#err2");

	var sourceBoard = extractBoard($("#source_board").val());
	var destinationBoard = extractBoard($("#destination_board").val());

	var pinLink = $("#pin_link").val() ? $("#pin_link").val() != false : null;
	var description = $("#description").val() ? $("#description").val() : null;

	if (sourceBoard == false) {
		err1.html("Enter a valid source board");
		return;
	} else if (destinationBoard == false) {
		err2.html("Enter a valid destination board");
		return;
	}

	$("#pin-button").attr("disabled", true);

	$.get('check-last-pin-status', {source: sourceBoard, destination: destinationBoard},function (data) {
		console.log(data);
		if (data.code == 200 && data.cursor != "") {
			cont = confirm("You have pinned " + data.pins_copied + " pins from this board. Do you want to continue with the next one? Press Cancel to restart.");

			console.log(cont);

			if (cont)
				cursor = data.cursor;
		}

		$.post("pin-it", {source: sourceBoard, destination: destinationBoard, requests_left: requestsLeft, cont: cont, cursor: cursor, pin_link: pinLink, description: description}, function(result) {
			console.log(result);
			if (result.code == 401) {
				window.location.href = result.data;
			} else if (result.code == 500) {
				$('#status').text('Unexpected error occurred: Please contact the developer.');
			} else if (result.code == 204) {
				$('#status').text(result.data);
			} else {
				updater();
			}
		});
	});
}

function extractBoard(board) {
	if (board.substring(0,6) == "https:") {
		var board_parts = board.split("/");
		board = board_parts[3] + "/" + board_parts[4];
	} else if (board.replace(/^\/|\/$/g, "").split("/").length == 2) {
		board = board.replace(/^\/|\/$/g, "");
	} else {
		return false;
	}
	return board;
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