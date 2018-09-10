function update_branch() {
    $("#uploads").text("");
    $("#monolingual").text("");
    $("#parallel").text("");
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
	let subdir = id_name+"-_-"+directories[i];
	$("#"+id_name).append('<li id="'+subdir+'" opened="none">'+directories[i]+'</li>');
	$("#"+subdir).on("click", function() {
	    open_or_close(subdir);
	});
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
	    let subdir_id = subdir+"-_-"+subdirs[i]
	    subdir_list += '<li id="'+subdir_id+'" opened="none">'+subdirs[i]+'</li>';
	    $(document).on("click", "#"+subdir_id, function() {
		open_or_close(subdir_id);
	    });
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

let usernumber = 0

$("#adduser").on("click", function() {
    $("#selected-users").append('<li id="user' + usernumber + '">' + $("#userlist").val() + '<button type="button" style="padding: 0px">x</button></li>');
    let userid = "#user" + usernumber
    $(document).on("click", userid, function() {
	$(userid).remove();
    });
    usernumber++;
});

update_branch();
