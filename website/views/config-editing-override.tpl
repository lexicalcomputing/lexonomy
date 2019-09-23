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
        <script type="text/javascript" src="../../../widgets/editing-override.js"></script>
        <link type="text/css" rel="stylesheet" href="../../../widgets/pillarform.css" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.46.0/codemirror.min.css" integrity="sha256-I8NyGs4wjbMuBSUE40o55W6k6P7tu/7G28/JGUUYCIs=" crossorigin="anonymous" />
        <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.46.0/codemirror.min.js" integrity="sha256-OMbqhJ5GYA+UQ2a9UE9iXHA1kn3hlZCFL5aZmpSp/+M=" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.46.0/mode/javascript/javascript.min.js" integrity="sha256-h2CaV12bheEEc7Ao3zF6MntAbDLJkPoFR+h+nHvQUqA=" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.46.0/mode/css/css.min.js" integrity="sha256-mSK/ZI2z8KrKSjKaCmUIVLJVH5ocYo92K8Zjam/tCyc=" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.46.0/addon/edit/matchbrackets.min.js" integrity="sha256-hfP/jiEfynvmq3cvlRWLdhKYZhpVVhYc2g+/ajTXdH0=" crossorigin="anonymous"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.46.0/addon/display/fullscreen.css" integrity="sha256-SpuaNYgDjBMdeyjrjtsC+U5fpSDpftPNv7oO8HQvG7w=" crossorigin="anonymous" />
        <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.46.0/addon/display/fullscreen.min.js" integrity="sha256-7RNoYfNeoShOS6Ry3d3ek7uRgARlr7oRYXbR1ni/ZEg=" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.46.0/addon/selection/active-line.min.js" integrity="sha256-D6+2VpcCER+2VNRAVaEznj9zfwUlvgCp9q+K+ELnry4=" crossorigin="anonymous"></script>
        <script type="text/javascript">
        Screenful.Editor.singleton=true;
        Screenful.Editor.entryID="editing";
        Screenful.Editor.leaveUrl="../../../{{dictID}}/config/";
        Screenful.Editor.readUrl="../../../{{dictID}}/configread.json";
        Screenful.Editor.updateUrl="../../../{{dictID}}/configupdate.json";
        Screenful.Editor.editor=function(div, entry){
            EditingOverride.change=Screenful.Editor.changed;
            EditingOverride.render(div, entry.content);
        };
        Screenful.Editor.harvester=function(div){
            return JSON.stringify(EditingOverride.harvest(div));
        };
        Screenful.Editor.allowSourceCode=false;
        Screenful.Editor.toolbarLinks=[
            {image: "../../../furniture/cancel.png", caption: "Disable entry editor customizations...", href: "../../../{{dictID}}/config/editing/"}
        ];
        </script>
        <link type="text/css" rel="stylesheet" href="../../../furniture/ui.css" />
    </head>
    <body>
         %include("header.tpl", user=user, dictID=dictID, dictTitle=dictTitle, current="config", configTitle="Entry editor", configUrl="editing-override", rootPath="../../../")
    </body>
</html>
