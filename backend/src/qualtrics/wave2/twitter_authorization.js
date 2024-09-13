Qualtrics.SurveyEngine.addOnload(function()
{
	/*Place your JavaScript here to run when the page loads*/
	this.hideNextButton();
	this.hidePreviousButton();
});
Qualtrics.SurveyEngine.addOnReady(function()
{
	/*Place your JavaScript here to run when the page is fully displayed*/
	var element = document.getElementById("twitter-login-btn");
	element.onclick = function(event) {
		var oauth_token_tt = ""
		var xmlHttp = new XMLHttpRequest();
    	xmlHttp.onreadystatechange = function() {
        	if (xmlHttp.readyState == 4 && xmlHttp.status == 200){
				oauth_token_tt = xmlHttp.responseText;
				console.log('${e://Field/mode}')
				Qualtrics.SurveyEngine.setEmbeddedData( 'oauth_token', xmlHttp.responseText);
				let popup = window.open("https://colon.umd.edu/qualrender?oauth_token="+oauth_token_tt+"&mode=DEMO&participant_id=${e://Field/participant_id}&assignment_id=${e://Field/assignment_id}&project_id=${e://Field/project_id}", "hello", "width=500,height=500");
				if(!popup) 
					document.getElementById("popup").hidden = false;
				var count = 1;
				var pollTimer = window.setInterval(function() {
					count = count + 1;
					if (count == 100){
						window.clearInterval(pollTimer);
						document.getElementById("fail").hidden = false;
					}
					window.setTimeout(function() {
						var xmlHttp2 = new XMLHttpRequest();
						xmlHttp2.onreadystatechange = function() {
							if (xmlHttp2.readyState == 4 && xmlHttp2.status == 200){
								if(xmlHttp2.responseText != "####"){
									console.log(xmlHttp2.responseText);
									if(popup)
										popup.close();
									window.clearInterval(pollTimer);
									if(xmlHttp2.responseText == "error"){
										document.getElementById("fail").hidden = false;
									}
									else{
										Qualtrics.SurveyEngine.setEmbeddedData( 'screename', xmlHttp2.responseText.split("$$$")[0]);
										Qualtrics.SurveyEngine.setEmbeddedData( 'userid', xmlHttp2.responseText.split("$$$")[1]);
										Qualtrics.SurveyEngine.setEmbeddedData( 'workerid', xmlHttp2.responseText.split("$$$")[2]);
										Qualtrics.SurveyEngine.setEmbeddedData( 'access_token', xmlHttp2.responseText.split("$$$")[3]);
										Qualtrics.SurveyEngine.setEmbeddedData( 'access_token_secret', xmlHttp2.responseText.split("$$$")[4]);
										Qualtrics.SurveyEngine.setEmbeddedData( 'file_number', xmlHttp2.responseText.split("$$$")[6]);
										setTimeout(function () {jQuery('#NextButton').click();},200);
									}
								}
							}
						}
						xmlHttp2.open("GET", 'https://colon.umd.edu/auth/getscreenname?oauth_token='+oauth_token_tt, true);
						xmlHttp2.send(null);
					},1);
				}, 1000);
			}
    	}
		xmlHttp.open("GET", 'https://colon.umd.edu/qualauth/', true);
    	xmlHttp.send(null);
	}
});
Qualtrics.SurveyEngine.addOnUnload(function()
{
	/*Place your JavaScript here to run when the page is unloaded*/
});