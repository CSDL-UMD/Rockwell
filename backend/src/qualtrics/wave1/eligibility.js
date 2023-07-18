Qualtrics.SurveyEngine.addOnload(function()
{
	/*Place your JavaScript here to run when the page loads*/
	this.hideNextButton();
	this.hidePreviousButton();
});
Qualtrics.SurveyEngine.addOnReady(function()
{
	/*Place your JavaScript here to run when the page is fully displayed*/
	var xmlHttp1 = new XMLHttpRequest();
	xmlHttp1.onreadystatechange = function() {
		if (xmlHttp1.readyState == 4 && xmlHttp1.status == 200){
			responsee = JSON.parse(xmlHttp1.responseText);
			document.getElementById('labelprogress').innerHTML = 'Completed'
			document.getElementById('file').innerHTML = '100%'
			document.getElementById('file').value = 100

			setTimeout(function () {jQuery('#NextButton').click();},200);
		}
	}
	xmlHttp1.open("GET", 'https://colon.umd.edu/hometimeline?worker_id=${e://Field/workerid}&max_id=INITIAL&collection_started=INITIAL&file_number=${e://Field/file_number}&num_tweets_cap=${e://Field/cap}', true); // true for asynchronous
	xmlHttp1.send(null);
});
Qualtrics.SurveyEngine.addOnUnload(function()
{
	/*Place your JavaScript here to run when the page is unloaded*/
});