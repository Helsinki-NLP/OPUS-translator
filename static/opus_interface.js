function update_branch() {
    $("#uploads").text("");
    $("#monolingual").text("");
    $("#parallel").text("");
    $("#branch").val($("#choose-branch").val());
    $.getJSON("https://vm1617.kaj.pouta.csc.fi/get_branch", {
	corpusname: $("#corpusname").text(),
	branch: $("#choose-branch").val()
    }, function(data) {
	subdir_to_list(data.uploads, "uploads");
	subdir_to_list(data.monolingual, "monolingual");
	subdir_to_list(data.parallel, "parallel");
    });
}

function subdir_to_list(directories, id_name){
    for (let i=0; i<directories.length; i++) {
	let subdir = id_name+"-_-"+directories[i][0];
	subdir = subdir.replace(/\./g, "-_DOT_-");	
	$("#"+id_name).append('<li id="'+subdir+'" ptype="' + directories[i][1] + '" opened="none">'+directories[i][0]+'</li>');
	let ptype = directories[i][1];
	if (ptype == "dir") {
	    $("#"+subdir).on("click", function() {
		open_or_close(subdir);
	    });
	} else if (ptype == "file"){
	    $("#"+subdir).on("click", function() {
		console.log("this is a file");
	    });
	}
    }
}

function open_subdir(subdir) {
    $.getJSON("https://vm1617.kaj.pouta.csc.fi/get_subdirs", {
	corpusname: $("#corpusname").text(),
	branch: $("#choose-branch").val(),
	subdir: "/"+subdir
    }, function(data) {
	let subdirs = data.subdirs;
	let subdir_list = '<li id="'+subdir+'_list"><ul id="'+subdir+'_list2" style="padding-left: 20px; list-style-type: none">'
	for (let i=0; i<subdirs.length; i++) {
	    let subdir_id = subdir+"-_-"+subdirs[i][0]
	    subdir_id = subdir_id.replace(/\./g, "-_DOT_-");
	    subdir_list += '<li id="'+subdir_id+'" ptype="'+subdirs[i][1]+'" opened="none">'+subdirs[i][0]+'</li>';
	    let ptype = subdirs[i][1];
	    if (ptype == "dir") {
		$(document).on("click", "#"+subdir_id, function() {
		    open_or_close(subdir_id);
		});
	    } else if (ptype == "fil") {
		$(document).on("click", "#"+subdir_id, function() {
		    $("#filedisplay-header-cell").css("display", "");
		    $("#filedisplay-content-cell").css("display", "");
		    $("#monolingual-header-cell").css("display", "none");
		    $("#monolingual-tree-cell").css("display", "none");
		    $("#parallel-header-cell").css("display", "none");
		    $("#parallel-tree-cell").css("display", "none");
		});
	    }
	}
	subdir_list += "</ul></li>";
	$("#"+subdir).after(subdir_list);
    });
}

function open_or_close(subdir) {
    if ($("#"+subdir).attr("opened") == "none") {
	open_subdir(subdir);
	$("#"+subdir).attr("opened", "true");
    } else if ($("#"+subdir).attr("opened") == "true") {
	$("#"+subdir+"_list").css("display", "none");
	$("#"+subdir).attr("opened", "false");
	/*
	$("#"+subdir+"_list2").children().each(function( index ) {
	    $(document).off("click", "#"+$(this).attr("id"));
	});
	$("#"+subdir+"_list").remove();
	$("#"+subdir).attr("opened", "none");
	*/
    } else if ($("#"+subdir).attr("opened") == "false") {
	$("#"+subdir+"_list").css("display", "block");
	$("#"+subdir).attr("opened", "true");
    }
}

$("#choose-branch").on("change", function() {
    update_branch();
});

$("#choose-branch").val(decodeURIComponent(window.location.search.substring(1)).split("&")[0].split("=")[1]);

update_branch();
