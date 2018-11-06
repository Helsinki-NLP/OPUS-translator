function translate() {
    $("#asksuggestion").css("display", "none");
    $("#source").text("");

    $("#suggestion").val("");

    $("#trash-div").css("display", "none");
    
    let sentence = $("#sentence").val();
    
    let source_lan = $("#selected-source").attr("language");
    let target_lan = $("#selected-target").attr("language");
    var direction = source_lan + "-" + target_lan;

    if ($.inArray(direction, ["fi-fi", "sv-sv", "sv-no", "sv-da"]) != -1) {
	$("#translation").text(sentence);
    } else if ($.trim(sentence) != "") {
	$("#translation").css("font-style", "italic");
	$("#translation").text("Translating...");
	$.getJSON("https://translate.ling.helsinki.fi/translate", {
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
	    $("#suggestion").val(data.result);
	    $("#submissionmessage").text("");
	    $("#target-language-cell").find("[language="+data.target+"]").click()
	});
	return false;
    } else {
	$("#translation").text("");
	$("#suggestionbutton").css("display", "none");
	$("#reportbutton").css("display", "none");
	$("#submissionmessage").text("");
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
    $.getJSON("https://translate.ling.helsinki.fi/suggest", {
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
    $("#trash-div").css("display", "none");
    $("#asksuggestion").css("display", "block");
});

$("#reportbutton").on("click", function() {
    $("#asksuggestion").css("display", "none");
    $("#trash-div").css("display", "block");
    trash();
});

$("#report").on("click", function() {
    var sentence = coloredToBracketed();    
    $.getJSON("https://translate.ling.helsinki.fi/suggest", {
	direction: $("#sourcedirection").text(),
	sentence: sentence
    });
    $("#trash-div").css("display", "none");
    $("#submissionmessage").text("Bad sentence reported!");
});
    
var isDown = false;
$(document).mousedown(function() {
    isDown = true;
})
$(document).mouseup(function() {
    isDown = false;
});

function trash() {
    $("#words").html("");
    var buttons = 0;
    let words = [];
    let lines = $("#translation").val().split("\n");
    for (let i=0;i<lines.length;i++) {
	for (let j=0;j<lines[i].split(" ").length;j++) {
	    words.push(lines[i].split(" ")[j]);
	}
    }		 

    $.each(words, function(i, val) {
	if (val == ""){
	    $("#words").append('<br><br>');
	}
	
	var valid = "word" + buttons.toString();
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
    $("#words").append('<button id="'+wordid+'-word" class="word-button" style="border: none; padding: 0; font-size: 20px;">'+word+'</button> ');
}

function changeColor(word) {
    color = $("#"+word+"-word").css("color")
    if (color == "rgb(255, 0, 0)") {
	$("#"+word+"-word").css("color", "black");
    } else {
	$("#"+word+"-word").css("color", "red");
    }
}

$("#trash-sentence").on("click", function() {
    var color = "red";
    if ($("#word0-word").css("color") == "rgb(255, 0, 0)") {
	color = "black";
    }
    $(".word-button").each(function(index) {
	$(this).css("color", color);
    });
});

function coloredToBracketed() {
    var sentence = "";
    var prevRed = false;
    $(".word-button").each(function(index) {
	var color = $(this).css("color");
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
    console.log(sentence.trim());
    return sentence.trim();
}

$(".source-languages").on("click", function() {
    $(".source-languages").css("background-color", "");
    $(".source-languages").attr("id", "");
    $(this).css("background-color", "#D8D8D8");
    $(this).attr("id", "selected-source");
    let sourcelang = $(this).attr("language");
    let targetlang = $("#selected-target").attr("language");
    if (sourcelang == "fi" && targetlang == "fi" ) {
	$("#target-language-cell").find("[language=sv]").click()
    } else if (sourcelang == "sv" && $.inArray(targetlang, ["no", "sv", "da"]) != -1) {
	$("#target-language-cell").find("[language=fi]").click()
    }
});

$(".target-languages").on("click", function() {
    $(".target-languages").css("background-color", "");
    $(".target-languages").attr("id", "");
    $(this).css("background-color", "#D8D8D8");
    $(this).attr("id", "selected-target");
    let sourcelang = $("#selected-source").attr("language");
    let targetlang = $(this).attr("language");
    if (sourcelang == "fi" && targetlang == "fi" ) {
	$("#source-language-cell").find("[language=sv]").click()
    } else if (sourcelang == "sv" && $.inArray(targetlang, ["no", "sv", "da"]) != -1) {
	$("#source-language-cell").find("[language=fi]").click()	
    }    
});
