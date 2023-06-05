Qualtrics.SurveyEngine.addOnload(function()
{
	/*Place your JavaScript here to run when the page loads*/
	document.getElementById("screenameinput2").value = "${e://Field/screename}";
	document.getElementById("screenameinput2").disabled = true;
	this.hideNextButton();
});

Qualtrics.SurveyEngine.addOnReady(function()
{
	/*Place your JavaScript here to run when the page is fully displayed*/
	document.getElementById("load-feed-btn").onclick = function(event) {
		var urll = 'http://colon.umd.edu/feed?attn=0&page=0&feedtype=S'
		var win = window.open(urll, 'window1');
		win.focus();
	}
	var count = 1;
	var pollTimer = window.setInterval(function() {
		count = count + 1;
		if (count == 10000){
			window.clearInterval(pollTimer);
			document.getElementById("fail").hidden = false;
		}
		window.setTimeout(function() {
			var xmlHttp2 = new XMLHttpRequest();
			var worker_id = "${e://Field/workerid}";
			xmlHttp2.onreadystatechange = function() {
				if (xmlHttp2.readyState == 4 && xmlHttp2.status == 200){
					if(xmlHttp2.responseText == "YES"){
						console.log(xmlHttp2.responseText);
						window.clearInterval(pollTimer);
						jQuery("#NextButton").show();
					}
				}
			}
			xmlHttp2.open("GET", 'https://colon.umd.edu/completedcheck?worker_id='+worker_id, true);
			xmlHttp2.send(null);
		},1);
	}, 1000);
});

Qualtrics.SurveyEngine.addOnUnload(function()
{
	/*Place your JavaScript here to run when the page is unloaded*/
});