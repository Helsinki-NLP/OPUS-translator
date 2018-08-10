function translate() {
    $("#asksuggestion").css("display", "none");
    $("#source").text("");
    $("#suggestionmessage").text("");
    $("#reportmessage").text("");
    $("#suggestion").val("");
    $("#trash-div").css("display", "none");
    var sentence = $("#sentence").val();
    let direction = $("#direction").val();
    if ($.trim(sentence) != "") {
	$("#translation").css("font-style", "italic");
	$("#translation").text("Translating...");
	$.getJSON("https://vm1617.kaj.pouta.csc.fi/translate", {
	    sent: sentence,
	    direction: direction
	}, function(data) {
	    $("#suggestionbutton").css("display", "block");
	    $("#reportbutton").css("display", "block");
	    $("#source").val(sentence);
	    $("#sourcedirection").text(direction);
	    $("#status").text("");
	    $("#translation").css("font-style", "normal");
	    $("#translation").text(data.result);
	});
	return false;
    } else {
	$("#translation").text("");
	$("#suggestionbutton").css("display", "none");
	$("#reportbutton").css("display", "none");
    }
}

$("#translate").on("click", function() {
    translate();
});

$("#sentence").keyup(function(ev) {
    if (ev.ctrlKey && ev.which === 13) {
	translate();
    }
});

$("#direction").on('change', function() {
    translate();
});

function suggest() {
    $.getJSON("https://vm1617.kaj.pouta.csc.fi/suggest", {
	direction: $("#sourcedirection").text(),
	source: $("#source").val(),
	suggestion: $("#suggestion").val()
    });
    $("#suggestionmessage").text("Translation added!");
    $("#asksuggestion").css("display", "none");
    $("#suggestionbutton").css("display", "none");
}

$("#suggest").on("click", function() {
    suggest();
});

$("#suggestion").keyup(function(ev) {
    if (ev.which === 13) {
	suggest();
    }
});

$("#suggestionbutton").on("click", function() {
    if ($("#suggestionmessage").text()=="") {
	$("#trash-div").css("display", "none");
	$("#asksuggestion").css("display", "block");
    }
});

$("#reportbutton").on("click", function() {
    if ($("#reportmessage").text()=="") {
	$("#asksuggestion").css("display", "none");
	$("#trash-div").css("display", "block");
	trash();
    }
});

$("#report").on("click", function() {
    let sentence = coloredToBracketed();
    console.log(sentence);
    $.getJSON("https://vm1617.kaj.pouta.csc.fi/report", {
	direction: $("#sourcedirection").text(),
	source: $("#source").val(),
	sentence: sentence
    });
    $("#trash-div").css("display", "none");
    $("#reportmessage").text("Bad sentence reported!");
    $("#reportbutton").css("display", "none");
});
    
let isDown = false;
$(document).mousedown(function() {
    isDown = true;
})
$(document).mouseup(function() {
    isDown = false;
});

function trash() {
    $("#words").html("");
    let buttons = 0;
    words = $("#translation").val().split(" ");
    $.each(words, function(i, val) {

	let valid = "word" + buttons.toString();
	buttons += 1;

	createButton(val, valid);
	$("#"+valid+"-word").mouseover(function() {
	    if (isDown) {
		changeColor(valid);
	    }
	});
	$("#"+valid+"-word").mousedown(function() {
	    changeColor(valid);
	});
    });
}

function createButton(word, wordid) {
    let color = $("body").css("background-color");
    word = word.split("\n");
    if (word[word.length-1] != "") {
	for (let i=0; i<word.length; i++) {
	    if (word[i] == "") {
		$("#words").append("<br>");
	    }
	}
	$("#words").append('<button id="'+wordid+'-word" class="word-button" style="border: none; padding: 0; margin: 0px 3px; font-size: 20px; background-color: '+color+';">'+word[word.length-1]+'</button>');
    }
}

function changeColor(word) {
    let color = $("#"+word+"-word").css("color")
    if (color == "rgb(255, 0, 0)") {
	$("#"+word+"-word").css("color", "black");
    } else {
	$("#"+word+"-word").css("color", "red");
    }
}

$("#trash-sentence").on("click", function() {
    let color = "black";
    $(".word-button").each(function(index) {
	if ($(this).css("color") != "rgb(255, 0, 0)") {
	    color = "red";
	}
    });
    $(".word-button").each(function(index) {
	$(this).css("color", color);
    });
});

function coloredToBracketed() {
    let sentence = "";
    let prevRed = false;
    $(".word-button").each(function(index) {
	let color = $(this).css("color");
	if (color == "rgb(255, 0, 0)") {
	    if (!prevRed) {
		sentence += "<rubbish>";
	    }
	    prevRed = true;
	}
	if (color != "rgb(255, 0, 0)") {
	    if (prevRed) {
		sentence = sentence.substring(0, sentence.length-1) + "</rubbish> ";
	    }
	    prevRed = false;
	}
	sentence = sentence + $(this).text() + " ";
	if (color == "rgb(255, 0, 0)" && index == $(".word-button").length-1) {
	    sentence = sentence.substring(0, sentence.length-1) + "</rubbish>";
	}
    });
    return sentence.trim();
}
















