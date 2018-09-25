function update_branch() {
    $(document).off();
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
    $("#importfile").css("display", "none");
    $("#importfile").text("import");
    $("#downloadfile").css("display", "none");
    let path = formulate_datapath(datapath);
    let inUploads = path.startsWith("/" + $("#corpusname").text() + "/" + $("#branch").val() + "/uploads/");
    $.getJSON("https://vm1617.kaj.pouta.csc.fi/get_metadata", {
	path: path
    }, function(data) {
	for (i=0; i<data.metadataKeys.length; i++) {
	    let key = data.metadataKeys[i];
	    if (key == "owner" && data.metadata[key] == data.username && inUploads) {
		$("#importfile").css("display", "inline");
	    } else if (key == "status" && data.metadata[key] == "imported" && inUploads) {
		$("#importfile").text("import again");
	    } else if (!inUploads) {
		$("#downloadfile").css("display", "inline");
	    }
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

function importFile(datapath) {
    let path = formulate_datapath(datapath);
    $.getJSON("https://vm1617.kaj.pouta.csc.fi/import_file", {
	path: path
    }, function(data) {
	$("#messages")[0].innerHTML = "";
	$("#messages").append('<li>File "' + path + "' imported</li>");
    });
    update_branch();
    showOrHideTrees("monolingual", "parallel", "", "show");
}

function deleteFile(datapath, subdirname) {
    let path = formulate_datapath(datapath);
    
    $.getJSON("https://vm1617.kaj.pouta.csc.fi/delete_file", {
	path: path
    }, function(data) {
	$("#messages")[0].innerHTML = "";
	$("#messages").append('<li>File "' + path + "' deleted</li>");
    });
    update_branch();
    if (subdirname == "uploads") {
	showOrHideTrees("monolingual", "parallel", "", "show");
    } else if (subdirname == "monolingual") {
	showOrHideTrees("uploads", "parallel", "", "show");
    } else if (subdirname == "parallel") {
	showOrHideTrees("uploads", "monolingual", "", "show");
    }    
}

function downloadFile(datapath, filename) {
    let path = formulate_datapath(datapath);
    window.location.href = "https://vm1617.kaj.pouta.csc.fi/download_file?path="+path+"&filename="+filename;
    /*
    console.log(path, filename);
    $.getJSON("https://vm1617.kaj.pouta.csc.fi/download_file", {
	path: path,
	filename: filename
    }, function(data) {
	console.log(data);
    });
    */
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
	    processFile(directories[i][0], subdir, id_name);
	}
    }
}

$("#searchcorpus").on("keyup", function() {
    if ($("#searchcorpus").val() != "") {
	$.getJSON("https://vm1617.kaj.pouta.csc.fi/search", {
	    corpusname: $("#searchcorpus").val()
	}, function(data) {
	    $("#searchresult")[0].innerHTML = "";
	    for (let i=0; i<data.result.length; i++) {
		$("#searchresult").append('<li><a href="/show_corpus/'+data.result[i]+'">'+data.result[i]+'</a></li>');
	    }
	});
    } else {
	$("#searchresult")[0].innerHTML = "";
    }
});

$("#clonebranch").on("click", function() {
    let corpusname = $("#corpusname").text();
    let branchclone = $("#choose-branch").val();
    let username = $("#username").text();
    window.location.href = "https://vm1617.kaj.pouta.csc.fi/clone_branch?branch="+username+"&corpusname="+corpusname+"&branchclone="+branchclone;
    /*
    $.getJSON("https://vm1617.kaj.pouta.csc.fi/clone_branch", {
	path: path
    }, function(data) {
	console.log(data);
    });
    */
});

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
		processFile(subdirs[i][0], subdir_id, subdir);
	    }
	}
	
	if (subdirs.length == 0) {
	    subdir_list += "<li>---</li>";
	}
	
	subdir_list += "</ul></li>";

	$("#"+subdir).after(subdir_list);
    });
}

function processFile(filename, path, root) {
    $(document).on("click", "#"+path, function() {
	$("#filename").text(filename);
	showMetadata(path);
	$("#viewfile").text("view");
	$("#viewfile").attr("showing", "metadata");
	let subdirname = root.replace(/-_-.*/, "");
	if (subdirname == "uploads") {
	    showOrHideTrees("monolingual", "parallel", "uploads", "hide");
	    $("#importfile").off("click");
	    $("#importfile").on("click", function() {
		importFile(path);
	    });
	} else if (subdirname == "monolingual") {
	    showOrHideTrees("uploads", "parallel", "monolingual", "hide");
	} else if (subdirname == "parallel") {
	    showOrHideTrees("uploads", "monolingual", "parallel", "hide");
	}
	$("#viewfile").off("click");
	$("#viewfile").on("click", function() {
	    switchMetadataAndContent(path);
	});
	$("#deletefile").off("click");
	$("#deletefile").on("click", function() {
	    deleteFile(path, subdirname);
	});
	$("#downloadfile").off("click");
	$("#downloadfile").on("click", function() {
	    downloadFile(path, filename);
	});
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
console.log(branch);
if (branch != undefined) {
    $("#choose-branch").val(branch);
}

update_branch();
