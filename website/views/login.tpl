%import json
%JSON=json.dumps
<!DOCTYPE HTML>
<html>
	<head>
		% include("head.tpl")
		<title>Log in</title>
		<script type="text/javascript" src="../libs/screenful/screenful.js"></script>
		<script type="text/javascript" src="../libs/screenful/screenful-user.js"></script>
		<link type="text/css" rel="stylesheet" href="../libs/screenful/screenful-user.css" />
		<link type="text/css" rel="stylesheet" href="../libs/screenful/screenful.css" />
    <link type="text/css" rel="stylesheet" href="../libs/screenful/screenful-login.css" />
		<link type="text/css" rel="stylesheet" href="../libs/screenful/screenful-theme-blue.css" />
		<link type="text/css" rel="stylesheet" href="../furniture/public.css" />
		<script type="text/javascript">var rootPath="../";</script>
		<script type="text/javascript" src="../furniture/screenful-user-config.js"></script>
		<script type="text/javascript" src="../libs/screenful/screenful-login.js"></script>
		<script type="text/javascript" src="../libs/screenful/screenful-loc-en.js"></script>
		<script type="text/javascript">
		Screenful.Login.loginUrl="../login.json";
		Screenful.Login.redirectUrl="{{redirectUrl}}";
		Screenful.Login.sketchengineLoginPage="{{siteconfig['sketchengineLoginPage']}}";
		</script>
	</head>
	<body>
		<div id="header">
			<a class="sitehome" href="../">
%if siteconfig["readonly"]:
<span class="readonly">READ-ONLY</span>
%end
</a>
		  <div class="email ScreenfulUser"></div>
		</div>
	</body>
</html>
