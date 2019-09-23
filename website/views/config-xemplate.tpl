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
		<link type="text/css" rel="stylesheet" href="../../../libs/screenful/screenful-theme-blue.css" />
		<script type="text/javascript">
                Screenful.User.loggedin={{!JSON(user["loggedin"])}};
                Screenful.User.username="{{user['email']}}";
		</script>
		<script type="text/javascript">var rootPath="../../../";</script>
		<script type="text/javascript" src="../../../furniture/screenful-user-config.js"></script>
		<link type="text/css" rel="stylesheet" href="../../../libs/screenful/screenful-editor.css" />
		<script type="text/javascript" src="../../../libs/screenful/screenful-editor.js"></script>
		<script type="text/javascript" src="../../../widgets/xema-designer.js"></script>
		<link type="text/css" rel="stylesheet" href="../../../widgets/xema-designer.css" />
		<script type="text/javascript" src="../../../widgets/xemplate-designer.js"></script>
		<script type="text/javascript" src="../../../widgets/xemplatron.js"></script>
		<link type="text/css" rel="stylesheet" href="../../../widgets/xemplatron.css" />
		<script type="text/javascript">
		var xema={{!JSON(xema)}};
		var dictID="{{dictID}}";
		Screenful.Editor.singleton=true;
		Screenful.Editor.entryID="xemplate";
		Screenful.Editor.leaveUrl="../../../{{dictID}}/config/";
		Screenful.Editor.readUrl="../../../{{dictID}}/configread.json";
		Screenful.Editor.updateUrl="../../../{{dictID}}/configupdate.json";
		Screenful.Editor.editor=function(div, entry){
			XemplateDesigner.start(xema, entry.content);
			XemaDesigner.onchange=XemplateDesigner.onchange;
			if(entry.content._xsl || entry.content._css) { //the user is switching back from own stylesheet
				delete entry.content._xsl;
				delete entry.content._css;
				window.setTimeout(Screenful.Editor.changed, 100);
			}
		};
		Screenful.Editor.harvester=function(div){
			return JSON.stringify(XemplateDesigner.xemplate);
		};
		Screenful.Editor.allowSourceCode=true;
		Screenful.Editor.formatSourceCode=function(str){
			return Screenful.formatJson(str);
		};
		Screenful.Editor.validateSourceCode=function(str){
			return Screenful.isWellFormedJson(str);
		};
		Screenful.Editor.cleanupSourceCode=function(str){
			return JSON.parse(str);
		};
		Screenful.Editor.toolbarLinks=[
			{image: "../../../furniture/cog.png", caption: "Use your own stylesheet...", href: "../../../{{dictID}}/config/xemplate-override/"}
		];
		</script>
		<link type="text/css" rel="stylesheet" href="../../../furniture/ui.css" />
	</head>
	<body>
                %include("header.tpl", user=user, dictID=dictID, dictTitle=dictTitle, current="config", configTitle="Entry formatting", configUrl="xemplate", rootPath="../../../")
	</body>
</html>
