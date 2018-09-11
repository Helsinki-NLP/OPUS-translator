let usernumber = 0

$("#adduser").on("click", function() {
    $("#selected-users").append('<li id="user' + usernumber + '">' + $("#userlist").val() + '<button type="button" style="padding: 0px">x</button></li>');
    $("#members").val($("#members").val()+$("#userlist").val()+",");
    let userid = "#user" + usernumber
    $(document).on("click", userid, function() {
	let username = $(userid).text().substring(0, $(userid).text().length-1);
	$("#members").val($("#members").val().replace(username+",", ""));
	$(userid).remove();
    });
    usernumber++;
});
