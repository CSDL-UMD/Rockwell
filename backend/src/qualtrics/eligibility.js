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
			console.log(responsee)
			document.getElementById('labelprogress').innerHTML = 'User Timeline'
			document.getElementById('file').innerHTML = '35%'
			document.getElementById('file').value = 35
		
			var xmlHttp2 = new XMLHttpRequest();
			xmlHttp2.onreadystatechange = function() {
				if (xmlHttp2.readyState == 4 && xmlHttp2.status == 200){
					responsee = JSON.parse(xmlHttp2.responseText);
					console.log(JSON.parse(xmlHttp2.responseText));
					document.getElementById('labelprogress').innerHTML = 'Favourites'
					document.getElementById('file').innerHTML = '70%'
					document.getElementById('file').value = 70
			
					var xmlHttp3 = new XMLHttpRequest();
					xmlHttp3.onreadystatechange = function() {
						if (xmlHttp3.readyState == 4 && xmlHttp3.status == 200){
							responsee = JSON.parse(xmlHttp3.responseText);
							console.log(JSON.parse(xmlHttp3.responseText));
							document.getElementById('labelprogress').innerHTML = 'Completed'
							document.getElementById('file').innerHTML = '100%'
							document.getElementById('file').value = 100
				
							setTimeout(function () {jQuery('#NextButton').click();},1000);
						}
					}
					xmlHttp3.open("GET", 'https://rockwell.glciampaglia.com/api/favorites/${e://Field/access_token}&${e://Field/access_token_secret}&${e://Field/participantId}&${e://Field/assignmentId}&${e://Field/projectId}', true); // true for asynchronous
					//xmlHttp3.open("GET", 'https://rockwell.glciampaglia.com/api/favorites/${e://Field/access_token}&${e://Field/access_token_secret}&${e://Field/participantId}&${e://Field/assignmentId}&${e://Field/projectId}', true); // true for asynchronous
					xmlHttp3.send(null);
				}
			}
			xmlHttp2.open("GET", 'https://rockwell.glciampaglia.com/api/usertimeline/${e://Field/access_token}&${e://Field/access_token_secret}&${e://Field/participantId}&${e://Field/assignmentId}&${e://Field/projectId}', true); // true for asynchronous
			//xmlHttp2.open("GET", 'https://rockwell.glciampaglia.com/api/usertimeline/${e://Field/access_token}&${e://Field/access_token_secret}&${e://Field/participantId}&${e://Field/assignmentId}&${e://Field/projectId}', true); // true for asynchronous
			xmlHttp2.send(null);
		}
	}
	xmlHttp1.open("GET", 'https://rockwell.glciampaglia.com/api/hometimeline/${e://Field/access_token}&${e://Field/access_token_secret}&${e://Field/participantId}&${e://Field/assignmentId}&${e://Field/projectId}&INITIAL&INITIAL', true); // true for asynchronous
	//xmlHttp1.open("GET", 'https://rockwell.glciampaglia.com/api/hometimeline/${e://Field/access_token}&${e://Field/access_token_secret}&${e://Field/participantId}&${e://Field/assignmentId}&${e://Field/projectId}&INITIAL', true); // true for asynchronous
    xmlHttp1.send(null);
});
Qualtrics.SurveyEngine.addOnUnload(function()
{
	/*Place your JavaScript here to run when the page is unloaded*/
});