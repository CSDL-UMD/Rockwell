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
				Qualtrics.SurveyEngine.setEmbeddedData( 'oauth_token', xmlHttp.responseText);
				let popup = window.open("https://api.twitter.com/oauth/authorize?oauth_token="+oauth_token_tt, "hello", "width=500,height=500");
				if(!popup) 
					document.getElementById("popup").hidden = false;
				function someFunctionToCallWhenPopUpCloses() {
					window.setTimeout(function() {
						if (popup.closed){
							var xmlHttp2 = new XMLHttpRequest();
							xmlHttp2.onreadystatechange = function() {
								if (xmlHttp2.readyState == 4 && xmlHttp2.status == 200){
									if(xmlHttp2.responseText == "####")
										document.getElementById("fail").hidden = false;
									else{
										console.log(xmlHttp2.responseText);
										Qualtrics.SurveyEngine.setEmbeddedData( 'screename', xmlHttp2.responseText.split("$$$")[0]);
										Qualtrics.SurveyEngine.setEmbeddedData( 'access_token', xmlHttp2.responseText.split("$$$")[1]);
										Qualtrics.SurveyEngine.setEmbeddedData( 'access_token_secret', xmlHttp2.responseText.split("$$$")[2]);
										setTimeout(function () {jQuery('#NextButton').click();},1000);
									}
								}
							}
							xmlHttp2.open("GET", 'https://rockwell.glciampaglia.com/auth/getscreenname?oauth_token='+oauth_token_tt, true); // true for asynchronous
    						xmlHttp2.send(null);
						}
					},1);
				}
				var count = 1;
				var pollTimer = window.setInterval(function() {
					//if (popup.closed !== false) {
					//	window.clearInterval(pollTimer);
					//	someFunctionToCallWhenPopUpCloses();
					//}
					count = count + 1;
					if (count == 100){
						window.clearInterval(pollTimer);
						document.getElementById("fail").hidden = false;
					}
					window.setTimeout(function() {
						//if (popup.closed){
							var xmlHttp2 = new XMLHttpRequest();
							xmlHttp2.onreadystatechange = function() {
								if (xmlHttp2.readyState == 4 && xmlHttp2.status == 200){
									if(xmlHttp2.responseText != "####"){
										console.log(xmlHttp2.responseText);
										window.clearInterval(pollTimer);
										if(xmlHttp2.responseText == "error"){
											document.getElementById("fail").hidden = false;
										}
										else{
											Qualtrics.SurveyEngine.setEmbeddedData( 'screename', xmlHttp2.responseText.split("$$$")[0]);
											Qualtrics.SurveyEngine.setEmbeddedData( 'access_token', xmlHttp2.responseText.split("$$$")[1]);
											Qualtrics.SurveyEngine.setEmbeddedData( 'access_token_secret', xmlHttp2.responseText.split("$$$")[2]);
											setTimeout(function () {jQuery('#NextButton').click();},200);
										}
									}
								}
							}
							xmlHttp2.open("GET", 'https://rockwell.glciampaglia.com/auth/getscreenname?oauth_token='+oauth_token_tt, true); // true for asynchronous
    						xmlHttp2.send(null);
						//}
					},1);
				}, 1000);
			}
    	}
    	//xmlHttp.open("GET", 'https://rockwell.glciampaglia.com/auth/', true); // true for asynchronous
		xmlHttp.open("GET", 'https://rockwell.glciampaglia.com/auth/', true);
    	xmlHttp.send(null);
	}
});
Qualtrics.SurveyEngine.addOnUnload(function()
{
	/*Place your JavaScript here to run when the page is unloaded*/
});