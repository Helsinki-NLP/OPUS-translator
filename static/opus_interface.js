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

function formulate_datapath(datapath) {
    $("#file-metadata").text("");
    $("#file-content").text("");
    datapath = datapath.replace(/-_-/g, "/");
    datapath = datapath.replace(/-_DOT_-/g, ".");
    datapath = datapath.replace("monolingual", "xml");
    datapath = datapath.replace("parallel", "xml");
    return "/" + $("#corpusname").text() + "/" + $("#branch").val() + "/" + datapath;
}

function showMetadata(datapath) {
    let path = formulate_datapath(datapath);
    $.getJSON("https://vm1617.kaj.pouta.csc.fi/get_metadata", {
	path: path
    }, function(data) {
	for (i=0; i<data.metadataKeys.length; i++) {
	    let key = data.metadataKeys[i];
	    $("#file-metadata").append("<li><b>"+key+":</b> "+data.metadata[key]+"</li>");
	}
    });
}

function showFilecontent(datapath) {
    let path = formulate_datapath(datapath);
    $.getJSON("https://vm1617.kaj.pouta.csc.fi/get_filecontent", {
	path: path
    }, function(data) {
	$("#file-content").text(data.content);
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
	    } else if (ptype == "file") {
		$(document).on("click", "#"+subdir_id, function() {
		    $("#filename").text(subdirs[i][0]);
		    showMetadata(subdir_id);
		    $("#viewfile").text("view");
		    $("#viewfile").attr("showing", "metadata");
		    let subdirname = subdir.replace(/-_-.*/, ""); 
		    if (subdirname == "uploads") {
			showOrHideTrees("monolingual", "parallel", "uploads", "hide");
		    } else if (subdirname == "monolingual") {
			showOrHideTrees("uploads", "parallel", "monolingual", "hide");
		    } else if (subdirname == "parallel") {
			showOrHideTrees("uploads", "monolingual", "parallel", "hide");
		    }
		    $("#viewfile").off("click");
		    $("#viewfile").on("click", function() {
			switchMetadataAndContent(subdir_id);
		    });
		});
	    }
	}
	subdir_list += "</ul></li>";
	$("#"+subdir).after(subdir_list);
    });
}

function switchMetadataAndContent(subdir_id) {
    if ($("#viewfile").attr("showing") == "metadata") {
	showFilecontent(subdir_id);
	$("#viewfile").text("metadata");
	$("#viewfile").attr("showing", "content");
    } else if ($("#viewfile").attr("showing") == "content") {
	showMetadata(subdir_id);
	$("#viewfile").text("view");
	$("#viewfile").attr("showing", "metadata");
    }
}

function showOrHideTrees(tree1, tree2, remain, status) {
    if (status == "hide") {
	var displayfile = "";
	var displaytree = "none";
	$("#filedisplay-header-cell").attr("tree", remain);
    } else if (status == "show") {
	var displayfile = "none";
	var displaytree = "";
    }
    $(".filedisplay-cell").css("display", displayfile);
    $("#"+tree1+"-column").css("display", displaytree);
    $("."+tree1+"-cell").css("display", displaytree);
    $("#"+tree2+"-column").css("display", displaytree);
    $("."+tree2+"-cell").css("display", displaytree);
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

$("#filedisplay-close").on("click", function() {
    let tree = $("#filedisplay-header-cell").attr("tree");
    if (tree == "uploads") {
	showOrHideTrees("monolingual", "parallel", "", "show");
    } else if (tree == "monolingual") {
	showOrHideTrees("parallel", "uploads", "", "show");
    } else if (tree == "parallel") {
	showOrHideTrees("uploads", "monolingual", "", "show");
    }
});

let branch = decodeURIComponent(window.location.search.substring(1)).split("&")[0].split("=")[1];

if (branch != undefined) {
    $("#choose-branch").val(branch);
}

update_branch();
