%import json
%JSON=json.dumps
<!DOCTYPE HTML>
<html>
	<head>
		%include("head.tpl")
		<title>{{dictTitle}}</title>
		<script type="text/javascript" src="../../../libs/screenful/screenful.js"></script>
    <link type="text/css" rel="stylesheet" href="../../../libs/screenful/screenful.css" />
		<script type="text/javascript" src="../../../libs/screenful/screenful-loc-en.js"></script>
		<script type="text/javascript" src="../../../libs/screenful/screenful-user.js"></script>
		<link type="text/css" rel="stylesheet" href="../../../libs/screenful/screenful-user.css" />
		<script type="text/javascript" src="../../../libs/screenful/screenful-progress.js"></script>
		<link type="text/css" rel="stylesheet" href="../../../libs/screenful/screenful-progress.css" />
		<link type="text/css" rel="stylesheet" href="../../../libs/screenful/screenful-theme-blue.css" />
		<script type="text/javascript">
                Screenful.User.loggedin={{!JSON(user["loggedin"])}};
                Screenful.User.username="{{user['email']}}";
		Screenful.Progress.message="Lexonomy is re-indexing your dictionary.";
		Screenful.Progress.actionUrl="../../../{{dictID}}/resave.json";
		Screenful.Progress.awayUrl="{{awayUrl}}";
		Screenful.Progress.totalTodo={{todo}};
		</script>
		<script type="text/javascript">var rootPath="../../../";</script>
		<script type="text/javascript" src="../../../furniture/screenful-user-config.js"></script>
		<link type="text/css" rel="stylesheet" href="../../../furniture/ui.css" />
	</head>
	<body>
                %include("header.tpl", user=user, dictID=dictID, dictTitle=dictTitle, current="", configTitle="", configUrl="", rootPath="../../../")
	</body>
</html>
