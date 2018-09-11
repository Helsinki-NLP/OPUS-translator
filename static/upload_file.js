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
    urlParam = url[i].split("=");
    if (urlParam[0] == "corpus") {
	var corpus = urlParam[1];
    }
    else if (urlParam[0] == "branch") {
	var branch = urlParam[1];
    }
}

updatePath();
