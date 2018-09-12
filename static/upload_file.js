function updatePath() {
    $("#path").val("/"+corpus+"/"+branch+"/uploads/"+$("#format").val()+"/"+$("#language").val()+"/"+$("#file").val().replace(/.*\\/, ""));
}

$("#format").on("change", function() {
    updatePath();
});

$("#language").on("change", function() {
    updatePath();
});

$("#file").on("change", function() {
    updatePath();
});

let url = decodeURIComponent(window.location.search.substring(1)).split("&");

for (i=0; i<url.length; i++) {
    let urlParam = url[i].split("=");
    console.log(urlParam);
    if (urlParam[0] == "corpus") {
	var corpus = urlParam[1];
    } else if (urlParam[0] == "branch") {
	var branch = urlParam[1];
    } else if (urlParam[0] == "language") {
	$("#language").val(urlParam[1]);
    } else if (urlParam[0] == "fileformat") {
	$("#format").val(urlParam[1]);
    } else if (urlParam[0] == "description") {
	$("#description").val(urlParam[1]);
    } else if (urlParam[0] == "translation" && urlParam[1] == "true") {
	$("#translation")[0].outerHTML = '<input id="translation" name="translation" type="checkbox" checked>';
    } else if (urlParam[0] == "autoimport" && urlParam[1] == "true") {
	$("#autoimport")[0].outerHTML = '<input id="autoimport" name="autoimport" type="checkbox" checked>';
    }
}

updatePath();
