let baseurl = window.location.protocol + "//" + window.location.host

function translate() {
    $("#asksuggestion").css("display", "none");
    $("#source").text("");

    let sentence = $("#sentence").text();
    
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
            $("#sentence").text("");
            $("#sentence").append(data.sentence);
            $("#translation").text("");
            $("#translation").append(data.result);

            console.log(data.n_seg);
            highlight_on_hover(data.n_seg);

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

function change_color(classname, color1, color2) {
    elms = document.getElementsByClassName(classname);
    len = elms.length;
    for(var i=0; i<len; i++) {
        elms[i].style.backgroundColor = color1;
        elms[i].parentElement.style.backgroundColor = color2;
    }
}

function highlight_on_hover(n_seg) {
    for(var i=0; i<n_seg; i++) {
        elms = document.getElementsByClassName("seg"+i);
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
