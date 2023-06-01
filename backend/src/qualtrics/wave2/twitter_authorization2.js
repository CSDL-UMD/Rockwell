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
});

Qualtrics.SurveyEngine.addOnUnload(function()
{
	/*Place your JavaScript here to run when the page is unloaded*/
});