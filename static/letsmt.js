let paramdir = window.location.search.replace(/\%2F/g, "/").replace("?directory=", "")
if (paramdir != "") {
    $("#command").val(paramdir);
    go();
}

function go() {
    $("#result").text("");
    if ($("#command").val() == "" || $("#command").val() == "/") {
	$("#result").append('<button id="subdir">group</button>');
	$("#result").append('<button id="subdir">storage</button>');
    } else {
	$.getJSON("https://vm1617.kaj.pouta.csc.fi/letsmt", {
	    method: $("#method").val(),
	    command: $("#command").val(),
	    action: $("#action").val(),
	    payload: $("#payload").val()
	}, function(data) {
	    let xmldoc = $.parseXML(data.result);
	    $xml = $(xmldoc);
	    let names = "";
	    $xml.find("name").each(function(index, elem) {
		let name = elem.innerHTML;
		if (name.endsWith(".xml")) {
		    $("#result").append('<button id="xmlfile">'+elem.innerHTML+'</button>');
		} else {
		    $("#result").append('<button id="subdir">'+elem.innerHTML+'</button>');
		}
		names = names + " " + elem.innerHTML;
	    });
	    $("#xmlresult").text(data.result);
	    $("#method").val("GET");
	});
    }
}

$("#go").on("click", function() {
    go();
});

$(document).on("click", "#subdir",  function() {
    $("#action").val("");
    $("#command").val($("#command").val()+"/"+this.innerHTML);
    go();
});

$(document).on("click", "#xmlfile",  function() {
    $("#action").val("&action=download&archive=0");
    $("#command").val($("#command").val()+"/"+this.innerHTML);
    go();
});

$("#back").on("click", function() {
    $("#action").val("");
    let command = $("#command").val()
    let i = command.lastIndexOf('/')
    command = command.substring(0, i);
    $("#command").val(command);
    go();
});

$("#showupload").on("click", function() {
    if ($("#fileupload").css("display") == "none") {
	$("#fileupload").css("display", "block");
	$("#directory").val($("#command").val());
    } else {
	$("#fileupload").css("display", "none");
    }
});

$("#file").on("change", function() {
    let directory = $("#directory").val();
    let filename = $("#file").val().replace(/.*\\/, "/");
    let path = directory + filename;
    path = path.replace(/\/\//, "/");
    $("#directory").val(path);
});

