function update_directories() {
    $.getJSON("https://vm1617.kaj.pouta.csc.fi/letsmt", {
	corpusname: $("#corpusname").text(),
	branch: $("#choose-branch").val()
    }, function(data) {
	let directories = data.testlist;
	console.log(directories);
    });
}

$("#choose-branch").on("change", function() {
    console.log("ok");
    update_directories()
});
