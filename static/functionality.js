let baseurl = window.location.protocol + "//" + window.location.host

$("#sentence").focus();

function translate() {
    $("#asksuggestion").css("display", "none");
    $("#source").text("");

    $("#suggestion").val("");

    $("#trash-div").css("display", "none");
    
    var sentence = $("#sentence")[0].innerText;
    $("#sentence")[0].innerHTML = sentence.replace(/\n/g, '<br>');
    
    let source_lan = $("#selected-source").attr("language");
    let target_lan = $("#selected-target").attr("language");
    var direction = source_lan + "-" + target_lan;

    /*
    if ($.inArray(direction, ["fi-fi", "sv-sv", "sv-no", "sv-da"]) != -1) {
        $("#translation").text(sentence);
    } else
    */
    if ($.trim(sentence) != "") {
        $("#translation").css("font-style", "italic");
        $("#translation").text("Translating...");
        $.getJSON(baseurl+"/translate", {
            sent: sentence,
            direction: direction,
            highlight: 0
        }, function(data) {
            $("#suggestionbutton").css("display", "block");
            $("#reportbutton").css("display", "block");
            $("#source").val(sentence);
            $("#sourcedirection").text(direction);
            $("#status").text("");

            if (data.all_segs != '') {
                $("#sentence")[0].innerHTML=data.source_seg;
            }
            $("#translation").css("font-style", "normal");
            $("#translation")[0].innerHTML=data.target_seg;

            $("#suggestion").val(data.result);
            $("#submissionmessage").text("");
            $("#target-language-cell").find("[language="+data.target+"]").click()

            highlight_on_hover(data.all_segs);

            highlight_detected(data.source);
        });
        return false;
    } else {
        $("#translation").text("");
        $("#suggestionbutton").css("display", "none");
        $("#reportbutton").css("display", "none");
        $("#submissionmessage").text("");
    }
}

function change_color(classnames, color1, color2) {
    classnames = classnames.split(' ');
    for(var j=0; j<classnames.length; j++) {
        elms = document.getElementsByClassName(classnames[j]);
        len = elms.length;
        for(var i=0; i<len; i++) {
            elms[i].style.backgroundColor = color1;
            elms[i].parentElement.style.backgroundColor = color2;
        }
    }
}

function highlight_on_hover(all_segs) {
    for(var i=0; i<all_segs.length; i++) {
        elms = document.getElementsByClassName("seg"+all_segs[i]);
        len = elms.length;
        for(var j=0; j<len; j++) {
            elms[j].onmouseover = function() {
                change_color(this.className, "grey", "silver");
            };
            elms[j].onmouseout = function() {
                change_color(this.className, "", "");
            };
        }
    }
}

function highlight_detected(source) {
    if ($("#selected-source").attr("language") == "DL") {
        $("#source-language-cell").find("[language=fi]").css({"border": "1px solid black", "background-color": ""});
        $("#source-language-cell").find("[language=sv]").css({"border": "1px solid black", "background-color": ""});
        $("#source-language-cell").find("[language="+source+"]").css({"border": "2px dashed black", "background-color": "#D8D8D8"});
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
    $.getJSON(baseurl+"/suggest", {
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
    $.getJSON(baseurl+"/suggest", {
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
    $(".source-languages").css({"background-color": "", "border": "1px solid black"});
    $(".source-languages").attr("id", "");
    $(this).css("background-color", "#D8D8D8");
    $(this).attr("id", "selected-source");
    let sourcelang = $(this).attr("language");
    let targetlang = $("#selected-target").attr("language");
    /*
    if (sourcelang == "fi" && targetlang == "fi" ) {
        $("#target-language-cell").find("[language=sv]").click()
    } else if (sourcelang == "sv" && $.inArray(targetlang, ["no", "sv", "da"]) != -1) {
        $("#target-language-cell").find("[language=fi]").click()
    }
    */
});

$(".target-languages").on("click", function() {
    $(".target-languages").css("background-color", "");
    $(".target-languages").attr("id", "");
    $(this).css("background-color", "#D8D8D8");
    $(this).attr("id", "selected-target");
    let sourcelang = $("#selected-source").attr("language");
    let targetlang = $(this).attr("language");
    /*
    if (sourcelang == "fi" && targetlang == "fi" ) {
        $("#source-language-cell").find("[language=sv]").click()
    } else if (sourcelang == "sv" && $.inArray(targetlang, ["no", "sv", "da"]) != -1) {
        $("#source-language-cell").find("[language=fi]").click()    
    }    
    */
});

function hideOrShowForm(formid, buttonid) {
    let formstyle = "none";
    let buttonstyle = {"background-color": "", "border": ""};
    if ($("#"+formid).css("display") == "none") {
        formstyle = "";
        buttonstyle = {"background-color": "#D8D8D8", "border": "1px solid black"};
    }
    $(".upload-form").css("display", "none");
    $(".show-form-button").css({"background-color": "", "border": ""});
    $("#"+formid).css("display", formstyle);
    $("#"+buttonid).css(buttonstyle);
}

$("#show-tm-form").on("click", function() {
    hideOrShowForm("upload-tm-form", "show-tm-form");
});

$("#show-td-form").on("click", function() {
    hideOrShowForm("upload-td-form", "show-td-form");
});

$("#show-url-form").on("click", function() {
    hideOrShowForm("upload-url-form", "show-url-form");
});
