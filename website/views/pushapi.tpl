<!DOCTYPE HTML>
<html>
	<head>
		<meta name="viewport" content="width=device-width, initial-scale=1.0" />
		<meta http-equiv="X-UA-Compatible" content="IE=edge" />
		%include("head.tpl")
		<title>Lexonomy Push API</title>
		<script type="text/javascript" src="libs/screenful/screenful.js"></script>
		<script type="text/javascript" src="libs/screenful/screenful-loc-en.js"></script>
		<link type="text/css" rel="stylesheet" href="furniture/public.css" />
	</head>
	<body>
		<div class="invelope top">
			<h1>Lexonomy Push API test page</h1>
			<p>{{siteconfig["baseUrl"]}}push.api</p>

			<hr/>
			<h2>Make a dictionary</h2>
			<textarea id="input_makeDict" style="font-size: 1rem; width: 100%; height: 11em; resize: vertical" spellcheck="false">{
  "email": "valselob@gmail.com",
  "apikey": "4HNA6VI6C9MROAENNYJQJPLL53HCAJMA",
  "command": "makeDict",
  "dictTitle": "My Pushy Dictionary",
  "dictBlurb": "Yet another dictionary draft.",
  "poses": ["n", "v", "adj", "adv"],
  "labels": ["colloquial", "formal", "mostly plural", "Irish English", "vulgar"]
}</textarea>
			<button onclick="makeDict()">Post</button> and watch your console.
			<script type="text/javascript">
			function makeDict(){
				//var json=JSON.parse($("#input_makeDict").val());
				var json=$("#input_makeDict").val();
				$.ajax("push.api", {method: "POST", contentType: "application/json", data: json, processData: false, dataType: "json"}).done(function(data){
					console.log(data);
				});
			}
			</script>

		<hr/>
		<h2>Create entries</h2>
		<textarea id="input_createEntries" style="font-size: 1rem; width: 100%; height: 9em; resize: vertical" spellcheck="false">{
  "email": "valselob@gmail.com",
  "apikey": "4HNA6VI6C9MROAENNYJQJPLL53HCAJMA",
  "command": "createEntries",
  "dictID": "jakobrno",
  "entryXmls": ["<heslo/>", "<heslo/>"]
}</textarea>
			<button onclick="createEntries()">Post</button> and watch your console.
			<script type="text/javascript">
			function createEntries(){
				var json=$("#input_createEntries").val();
				console.log(json);
				$.ajax("push.api", {method: "POST", contentType: "application/json", data: json, processData: false, dataType: "json"}).done(function(data){
					console.log(data);
				});
			}
			</script>

		</div>
	</body>
</html>
