%import json
%JSON=json.dumps
<!DOCTYPE HTML>
<html>
	<head>
		% include("head.tpl")
		<title>Sign up</title>
		<script type="text/javascript" src="../libs/screenful/screenful.js"></script>
		<script type="text/javascript" src="../libs/screenful/screenful-user.js"></script>
		<link type="text/css" rel="stylesheet" href="../libs/screenful/screenful-user.css" />
		<link type="text/css" rel="stylesheet" href="../libs/screenful/screenful.css" />
    <link type="text/css" rel="stylesheet" href="../libs/screenful/screenful-signup.css" />
		<link type="text/css" rel="stylesheet" href="../libs/screenful/screenful-theme-blue.css" />
		<link type="text/css" rel="stylesheet" href="../furniture/public.css" />
		<script type="text/javascript">var rootPath="../";</script>
		<script type="text/javascript" src="../furniture/screenful-user-config.js"></script>
		<script type="text/javascript" src="../libs/screenful/screenful-signup.js"></script>
		<script type="text/javascript" src="../libs/screenful/screenful-loc-en.js"></script>
		<script type="text/javascript">
		Screenful.Signup.actionUrl="../signup.json";
		Screenful.Signup.returnUrl="{{redirectUrl}}";
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
