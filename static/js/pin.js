var requests_left = 1000;
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

	var source_board = extractBoard($("#source_board").val());
	var destination_board = extractBoard($("#destination_board").val());

	if (source_board == false) {
	    err1.html("Enter a valid source board");
        return;
	} else if (destination_board == false) {
	    err2.html("Enter a valid destination board");
        return;
    }

    $.get('check-last-pin-status', {source: source_board, destination: destination_board},function (data) {
        console.log(data);
        if (data.code == 200 && data.cursor != "") {
            cont = confirm("You have pinned " + data.pins_copied + " pins from this board. Do you want to continue with the next one? Press Cancel to restart.");

            console.log(cont);

            if (cont)
                cursor = data.cursor;
        }

        $("#pin-button").attr("disabled", true);

        $.get("pin-it", {source: source_board, destination: destination_board, requests_left: requests_left, cont: cont, cursor: cursor}, function(result) {
            console.log(result);
            if (result.code == 401)
                window.location.href = result.data;
            updater();
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
            requests_left = data.data;
            console.log(requests_left);

            $("#pins-left").text(requests_left);
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