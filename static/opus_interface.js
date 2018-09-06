function update_branch() {
    $("#uploads").text("");
    $("#monolingual").text("");
    $("#parallel").text("");
    $.getJSON("https://vm1617.kaj.pouta.csc.fi/letsmt", {
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
	let subdir = id_name+"-_-"+directories[i];
	$("#"+id_name).append('<li id="'+subdir+'" opened="false">'+directories[i]+'</li>');
	$("#"+subdir).on("click", function() {
	    open_or_close(subdir);
	});
    }
}

function open_subdir(subdir) {
    $.getJSON("https://vm1617.kaj.pouta.csc.fi/letsmt", {
	corpusname: $("#corpusname").text(),
	branch: $("#choose-branch").val(),
	subdir: "/"+subdir
    }, function(data) {
	let subdirs = data.subdirs;
	let subdir_list = '<li id="'+subdir+'_list"><ul style="padding-left: 20px; list-style-type: none">'
	for (let i=0; i<subdirs.length; i++) {
	    let subdir_id = subdir+"-_-"+subdirs[i]
	    subdir_list += '<li id="'+subdir_id+'" opened="false">'+subdirs[i]+'</li>';
	    $(document).on("click", "#"+subdir_id, function() {
		open_or_close(subdir_id);
	    });
	}
	subdir_list += "</ul></li>";
	$("#"+subdir).after(subdir_list);
    });
}

function open_or_close(subdir) {
    if ($("#"+subdir).attr("opened") == "false") {
	$("#"+subdir).attr("opened", "true");
	open_subdir(subdir);
    } else {
	$("#"+subdir).attr("opened", "false");
	$("#"+subdir+"_list").remove();
    }
}

$("#choose-branch").on("change", function() {
    update_branch();
});

update_branch();
