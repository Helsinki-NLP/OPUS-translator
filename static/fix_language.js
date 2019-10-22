let baseurl = window.location.protocol + "//" + window.location.host

function translate() {
    $("#asksuggestion").css("display", "none");
    $("#source").text("");

    $("#suggestion").val("");

    $("#trash-div").css("display", "none");
    
    let sentence = $("#sentence").val();
    
    let source_lan = $("#selected-source").attr("language");
    var direction = source_lan + "-" + source_lan;

    if ($.trim(sentence) != "") {
        $("#translation").css("font-style", "italic");
        $("#translation").text("Translating...");
        $.getJSON(baseurl+"/translate", {
            sent: sentence,
            direction: direction
        }, function(data) {
            $("#source").val(sentence);
            $("#sourcedirection").text(direction);
            $("#status").text("");
            $("#translation").css("font-style", "normal");
            $("#translation").text(data.result);

            highlight_detected(data.source);
        });
        return false;
    } else {
        $("#translation").text("");
        $("#submissionmessage").text("");
    }
}

function highlight_detected(source) {
    if ($("#selected-source").attr("language") == "DL") {
        $(".source-languages").css({"background-color": "", "border": "1px solid black"});
        $("#source-language-cell").find("[language=DL]").css("background-color", "#D8D8D8");
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

$(".source-languages").on("click", function() {
    $(".source-languages").css({"background-color": "", "border": "1px solid black"});
    $(".source-languages").attr("id", "");
    $(this).css("background-color", "#D8D8D8");
    $(this).attr("id", "selected-source");
    let sourcelang = $(this).attr("language");
    let targetlang = $("#selected-target").attr("language");
});
