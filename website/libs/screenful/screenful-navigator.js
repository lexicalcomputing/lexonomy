Screenful.Navigator={
  start: function(){
    Screenful.createEnvelope();
    $("#envelope").html("<div id='midcontainer'></div><div id='leftcontainer'><span class='closer'>×</span><div id='leftbox'></div></div>");

    if(Screenful.Navigator.enableLeftPanel){
      $("#envelope").addClass("leftContainerCollapsed");
      $("#leftcontainer").on("click", function(e){
        if($("#envelope").hasClass("leftContainerCollapsed")) {
          $("#envelope").removeClass("leftContainerCollapsed").addClass("leftContainerExpanded");
          if(Screenful.Facetor) Screenful.Facetor.show();
        }
      });
      $("#leftcontainer > .closer").on("click", function(e){
        $("#envelope").removeClass("leftContainerExpanded").addClass("leftContainerCollapsed");
        var needReload=false;
        if(Screenful.Facetor) {
          if(Screenful.Facetor.harvest()) needReload=true;
          Screenful.Facetor.hide();
        }
        e.stopPropagation();
        if(needReload) Screenful.Navigator.list(e);
      });
    }

    $("#midcontainer").html("<div id='navbox'></div><div id='listbox'></div><div id='editbox'></div><div id='critbox' tabindex='0' style='display: none'></div>");
    $("#editbox").html("<iframe name='editframe' frameborder='0' scrolling='no' src='"+Screenful.Navigator.editorUrl+"'/>");
    $("#navbox").html("<div class='line1'><button class='iconOnly' id='butCritOpen'>&nbsp;</button><input id='searchbox' title='Ctrl + Shift + T'/><button id='butSearch' class='iconOnly mergeLeft noborder'>&nbsp;</buttton><button class='iconYes noborder' id='butCritRemove' style='display: none;'>"+Screenful.Loc.removeFilter+"</button></div>");
    $("#navbox").append("<div class='lineModifiers'><span class='clickable'><span class='current'></span> <span class='arrow'>▼</span></span><div class='menu' style='display: none'></div></div>");
    $("#searchbox").on("keydown", function(e){if(!e.altKey && !((e.ctrlKey || e.metaKey) && e.shiftKey)) e.stopPropagation()});
    $("#searchbox").on("keyup", function(event){
      if(event.which==27) $("#searchbox").val("");
      if(event.which==13) Screenful.Navigator.critGo(event);
    });
    $("#butSearch").on("click", Screenful.Navigator.critGo);
    $("#navbox").append("<div class='line2'><span id='countcaption'>0</span><button class='iconYes noborder' id='butReload'>"+Screenful.Loc.reload+"</button></div>");
    if(!(Screenful.Navigator.critEditor && Screenful.Navigator.critHarvester)) $("#butCritOpen").remove();
    $("#butCritOpen").on("click", Screenful.Navigator.critOpen);
    $("#butReload").on("click", Screenful.Navigator.reload);
    $("#critbox").html("<div id='editor'></div><div class='buttons'><button class='iconYes' id='butCritCancel'>"+Screenful.Loc.cancel+"</button><button class='iconYes' id='butCritGo'>"+Screenful.Loc.filter+"</button></div>");
    $("#critbox").on("keydown", function(e){e.stopPropagation(); e.preventDefault()});
    $("#butCritCancel").on("click", Screenful.Navigator.critCancel);
    $("#butCritGo").on("click", Screenful.Navigator.critGo);
    $("#butCritRemove").on("click", Screenful.Navigator.critRemove);
    if(Screenful.Navigator.modifiers && Screenful.Navigator.modifiers.length>0){
      $("#navbox").addClass("hasSearchModifiers");
      $("#listbox").addClass("hasSearchModifiers");
      $("#navbox .lineModifiers .clickable .current").html(Screenful.Navigator.modifiers[0].caption).data("value", Screenful.Navigator.modifiers[0].value);
      for(var i=0; i<Screenful.Navigator.modifiers.length; i++){
        var obj=Screenful.Navigator.modifiers[i];
        $("#navbox .lineModifiers .menu").append("<a href='javascript:void(null)' onclick='Screenful.Navigator.setModifier(\""+i+"\")'>"+obj.caption+"</a>")
      }
      $("#navbox .lineModifiers .clickable").on("click", function(e){
        var $mymenu=$(e.delegateTarget).closest(".lineModifiers").find(".menu");
        $(".menu").not($mymenu).slideUp();
        $mymenu.hide().slideDown();
        e.stopPropagation();
      });
    }
    $(document).on("click", function(e){
      $(".menu").slideUp();
    });
    if(Screenful.Navigator.critEditor && Screenful.Navigator.critHarvester) {
      $("#navbox .lineModifiers").addClass("hasCrits");
      Screenful.Navigator.critEditor(document.getElementById("editor"));
      Screenful.Navigator.critTemplate=Screenful.Navigator.critHarvester(document.getElementById("editor"));
    }
    window.setTimeout(Screenful.Navigator.list, 1000);
    $(document).on("click", function(){
      if(window.frames["editframe"] && window.frames["editframe"].Xonomy) window.frames["editframe"].Xonomy.clickoff();
    });

    //keyboard nav:
    $(document).on("keydown", function(e){
      if(e.which==37 && e.altKey){ //arrow down key
        e.preventDefault();
        Screenful.Navigator.focusEntryList();
      }
      if(e.which==39 && e.altKey){ //arrow right key
        if(window.frames["editframe"].Screenful) {
          e.preventDefault();
          window.frames["editframe"].focus();
        }
      }
      //console.log(e.which, e.ctrlKey, e.metaKey, e.altKey, e.altGraphKey, e.shiftKey);
      if(e.which==84 && (e.ctrlKey||e.metaKey) && e.shiftKey){ //T key
        e.preventDefault();
        e.stopImmediatePropagation();
        $("#searchbox").focus();
      }
      if(e.which==69 && (e.ctrlKey||e.metaKey) && e.shiftKey){ //E key
        if(window.frames["editframe"].Screenful){
          e.preventDefault();
          e.stopImmediatePropagation();
          window.frames["editframe"].$("#butEdit:visible").click();
          window.frames["editframe"].$("#butView:visible").click();
          window.frames["editframe"].focus();
        }
      }
      if(e.which==83 && (e.ctrlKey||e.metaKey) && e.shiftKey){ //S key
        if(window.frames["editframe"].Screenful){
          e.preventDefault();
          e.stopImmediatePropagation();
          window.frames["editframe"].$("#butSave:visible").click();
          window.frames["editframe"].focus();
        }
      }
      if(e.which==78 && (e.ctrlKey||e.metaKey) && e.shiftKey){ //N key
        if(window.frames["editframe"].Screenful){
          e.preventDefault();
          e.stopImmediatePropagation();
          window.frames["editframe"].$("#butNew:visible").click();
          window.frames["editframe"].focus();
        }
      }
    });
  },

  lastFocusedEntryID: "",
  focusEntryList: function(){
    if(Screenful.Navigator.lastFocusedEntryID && $("#listbox .entry[data-id=\""+Screenful.Navigator.lastFocusedEntryID+"\"]").length>0)
      $("#listbox .entry[data-id=\""+Screenful.Navigator.lastFocusedEntryID+"\"]").focus();
    else
      $("#listbox .entry").first().focus();
  },

  list: function(event, howmany, noSFX){
    if(!howmany) howmany=Screenful.Navigator.stepSize;
    Screenful.Navigator.lastStepSize=howmany;
    Screenful.status(Screenful.Loc.listing, "wait"); //"getting list of entries"
    var url=Screenful.Navigator.listUrl;
    var facets=null; if(Screenful.Facetor && $("#envelope").hasClass("leftContainerExpanded")) facets=Screenful.Facetor.harvest();
    var criteria=null; if(Screenful.Navigator.critHarvester) criteria=Screenful.Navigator.critHarvester(document.getElementById("editor"));
    var searchtext=$.trim($("#searchbox").val());
    var modifier=$.trim($("#navbox .lineModifiers .current").data("value"));
    if(criteria!=Screenful.Navigator.critTemplate) {
      $("#butCritOpen").addClass("on");
      $("#butCritRemove").show();
    } else {
      $("#butCritOpen").removeClass("on");
      $("#butCritRemove").hide();
    }
    if(searchtext!="") $("#butCritRemove").show();
    $.ajax({url: url, dataType: "json", method: "POST", data: {facets: facets, criteria: criteria, searchtext: searchtext, modifier: modifier, howmany: howmany}}).done(function(data){
      if(!data.success) {
        Screenful.status(Screenful.Loc.listingFailed, "warn"); //"failed to get list of entries"
      } else {
        $("#countcaption").html(data.total);
        var $listbox=$("#listbox").html("");
        data.entries.forEach(function(entry){
          var $item=$("<div class='entry' tabindex='0' data-id='"+entry.id+"'><div class='inside'>"+entry.id+"</div></div>").appendTo($listbox);
          $item.on("click", entry, Screenful.Navigator.openEntry);

          //entry title:
          Screenful.Navigator.renderer($item.find("div.inside").toArray()[0], entry, searchtext, modifier);

          //entry flag:
          if(Screenful.Navigator.flags && Screenful.Navigator.flags.length>0 && Screenful.Navigator.entryFlagUrl && Screenful.Navigator.extractEntryFlag){
            var $flagLink=$("<a class='entryFlagLink'></a>").prependTo($item);
            var flag=Screenful.Navigator.flagLookup( Screenful.Navigator.extractEntryFlag(entry) );
            $flagLink.css("background-color", flag.color);
            $flagLink.on("click", Screenful.Navigator.entryFlagLinkClick);
            var $menu=$("<div class='menu flagmenu' style='display: none'></div>").appendTo($item);
            Screenful.Navigator.flags.map(flag => {
              var $menuItem=$("<a href='javascript:void(null)'><span class='spot' style='background-color: "+flag.color+"'></span><span class='keyCaption'>"+flag.key+"</span>"+flag.label+"</a>").appendTo($menu);
              $menuItem.on("click", Screenful.Navigator.entryFlag);
              $menuItem.data("flag", flag);
            });
          }

          //entry menu:
          if(Screenful.Navigator.entryDeleteUrl){
            var $menuLink=$("<a class='entryMenuLink'>&middot;&middot;&middot;</a>").prependTo($item);
            $menuLink.on("click", Screenful.Navigator.entryMenuLinkClick);
            var $menu=$("<div class='menu entrymenu' style='display: none'></div>").appendTo($item);
            //delete:
            var $menuItem=$("<a href='javascript:void(null)'><span class='keyCaption'>Del</span>"+Screenful.Loc.delete+"</a>").appendTo($menu);
            $menuItem.on("click", Screenful.Navigator.entryDelete);
          }

        });
        if(!noSFX) $listbox.hide().fadeIn();
        if(data.entries.length<data.total){
          $listbox.append("<div id='divMore'><button class='iconYes' id='butMore'>"+Screenful.Loc.more+"</button></div>");
          $("#butMore").on("click", Screenful.Navigator.more);
        }
        if(window.frames["editframe"] && window.frames["editframe"].Screenful && window.frames["editframe"].Screenful.Editor) {
          var currentEntryID=window.frames["editframe"].Screenful.Editor.entryID;
          Screenful.Navigator.setEntryAsCurrent(currentEntryID);
        }
        Screenful.status(Screenful.Loc.ready);
        Screenful.Navigator.focusEntryList();

        //keyboard nav:
        $("#listbox .entry").on("keydown", function(e){
          if(e.which==40){ //arrow down key
            e.preventDefault();
            if(e.ctrlKey||e.metaKey) $("#listbox").scrollTop($("#listbox").scrollTop()+60);
            else {
              $(e.delegateTarget).next().focus();
              Screenful.Navigator.lastFocusedEntryID=$("#listbox .entry:focus").attr("data-id");
            }
          }
          if(e.which==38){ //arrow up key
            e.preventDefault();
            if(e.ctrlKey||e.metaKey) $("#listbox").scrollTop($("#listbox").scrollTop()-60);
            else {
              $(e.delegateTarget).prev().focus();
              Screenful.Navigator.lastFocusedEntryID=$("#listbox .entry:focus").attr("data-id");
            }
          }
          if(e.which==13){ //Enter key
            e.preventDefault(); $(e.delegateTarget).click();
          }
          if(e.which==46){ //Delete key
            e.preventDefault();
            Screenful.Navigator.entryDelete(e);
          }
          if(Screenful.Navigator.flags && Screenful.Navigator.flags.length>0 && Screenful.Navigator.entryFlagUrl){
            for(var i=0; i<Screenful.Navigator.flags.length; i++) {
              if(e.key==Screenful.Navigator.flags[i].key){
                e.preventDefault();
                Screenful.Navigator.entryFlag(e, Screenful.Navigator.flags[i].name)
              }
            }
          }
        });
        $("#listbox .entry").on("click", function(e){
          Screenful.Navigator.lastFocusedEntryID=$(e.delegateTarget).attr("data-id");
        });
      }
    });
  },
  lastStepSize: 0,
  more: function(event){
    Screenful.Navigator.list(event, Screenful.Navigator.lastStepSize+Screenful.Navigator.stepSize);
  },
  openEntry: function(event){
    var entry=event.data;
    if(window.frames["editframe"].Screenful) {
      window.frames["editframe"].Screenful.Editor.open(null, entry.id);
    }
  },
  setEntryAsCurrent: function(id){
    $("#listbox .entry").removeClass("current")
    $("div.entry[data-id=\""+id+"\"]").addClass("current");
  },

  previousCrit: null,
  critOpen: function(event){
    Screenful.Navigator.previousCrit=Screenful.Navigator.critHarvester(document.getElementById("editor")); //save previous criteria for later, in case the user cancels
    $("#curtain").show().one("click", Screenful.Navigator.critCancel);
    $("#critbox").show().focus();
  },
  critCancel: function(event){
    $("#critbox").hide();
    $("#curtain").hide();
    Screenful.Navigator.critEditor(document.getElementById("editor"), Screenful.Navigator.previousCrit); //restore previous criteria
  },
  critGo: function(event){
    $("#critbox").hide();
    $("#curtain").hide();
    $("#listbox").scrollTop(0);
    Screenful.Navigator.list();
  },
  critRemove: function(event){
    if(Screenful.Navigator.critEditor) Screenful.Navigator.critEditor(document.getElementById("editor"));
    $("#searchbox").val("");
    $("#listbox").scrollTop(0);
    Screenful.Navigator.list();
  },
  reload: function(event){
    $("#listbox").scrollTop(0);
    Screenful.Navigator.list();
  },
  setModifier: function(i){
    var obj=Screenful.Navigator.modifiers[i];
    $("#navbox .lineModifiers .clickable .current").html(obj.caption).data("value", obj.value);
    if($.trim($("#searchbox").val())!="") Screenful.Navigator.list();
  },

  refresh: function(entryID, action){
    if(entryID && action=="delete"){
      var $entry=$("div.entry[data-id=\""+entryID+"\"]");
      $entry.remove();
    } else if(entryID && action=="update" && Screenful.Navigator.listByIdUrl){
      $.ajax({url: Screenful.Navigator.listByIdUrl, dataType: "json", method: "POST", data: {id: entryID}}).done(function(data){
        if(data.success && data.entries.length>0 && data.entries[0].id==entryID) {
          var entry=data.entries[0];
          var $entry=$("div.entry[data-id=\""+entryID+"\"]");
          Screenful.Navigator.renderer($entry.find("div.inside").toArray()[0], entry, "", "");
          if(Screenful.Navigator.flags.length>0 && Screenful.Navigator.entryFlagUrl && Screenful.Navigator.extractEntryFlag){
            var flag=Screenful.Navigator.flagLookup( Screenful.Navigator.extractEntryFlag(entry) );
            $entry.find(".entryFlagLink").css("background-color", flag.color);
          }
        } else {
          Screenful.status(Screenful.Loc.listingFailed, "warn"); //"failed to get list of entries"
        }
      });
    } else {
      Screenful.Navigator.list(null, Screenful.Navigator.lastStepSize, true);
    }
  },

  entryMenuLinkClick: function(e){
    e.stopPropagation();
    var $menuLink=$(e.delegateTarget);
    var $entry=$menuLink.closest(".entry");
    var entryID=$entry.attr("data-id");
    var $menu=$entry.find(".entrymenu");
    $("#listbox .menu").not($menu).hide();
    $(".menu").not($menu).slideUp();
    $menu.hide().slideDown();
    e.stopPropagation();
  },
  entryDelete: function(arg){ //arg = event object or entryID
    var entryID=arg; if(typeof(arg)=="object") {
      entryID=$(arg.delegateTarget).closest(".entry").attr("data-id");
      $(".menu").hide();
      arg.stopPropagation();
    }
    if(window.frames["editframe"].Screenful && window.frames["editframe"].Screenful.Editor && window.frames["editframe"].Screenful.Editor.entryID==entryID) {
      window.frames["editframe"].Screenful.Editor.delete();
    } else {
      if(confirm(Screenful.Loc.deleteConfirm)){ //"are you sure?"
        Screenful.status(Screenful.Loc.deleting, "wait"); //"deleting entry..."
        $.ajax({url: Screenful.Navigator.entryDeleteUrl, dataType: "json", method: "POST", data: {id: entryID}}).done(function(data){
          if(!data.success) {
            Screenful.status(Screenful.Loc.deletingFailed, "warn"); //"failed to delete entry"
          } else {
            Screenful.status(Screenful.Loc.ready);
            var $entry=$("div.entry[data-id=\""+entryID+"\"]");
            if($entry.length>0){
              var $next=$entry.next(".entry"); if($next.length==0) $next=$entry.prev(".entry"); Screenful.Navigator.lastFocusedEntryID=$next.attr("data-id");
              Screenful.Navigator.refresh();
            }
          }
      	});
      }
    }
  },

  entryFlagLinkClick: function(e){
    e.stopPropagation();
    var $menuLink=$(e.delegateTarget);
    var $entry=$menuLink.closest(".entry");
    var entryID=$entry.attr("data-id");
    var $menu=$entry.find(".flagmenu");
    $("#listbox .menu").not($menu).hide();
    $(".menu").not($menu).slideUp();
    $menu.hide().slideDown();
    e.stopPropagation();
  },
  flagLookup: function(flagName){
    var ret=null;
    Screenful.Navigator.flags.map(flag => { if(flag.name==flagName) ret=flag; });
    return ret;
  },
  entryFlag: function(e, flagName){
    if(flagName===undefined) flagName=$(e.delegateTarget).data("flag").name;
    var flag=Screenful.Navigator.flagLookup(flagName);
    var entryID=$(e.delegateTarget).closest(".entry").attr("data-id");
    $(".menu").hide();
    e.stopPropagation();
    Screenful.status(Screenful.Loc.flagging, "wait"); //"flagging entry..."
    $.ajax({url: Screenful.Navigator.entryFlagUrl, dataType: "json", method: "POST", data: {id: entryID, flag: flag.name}}).done(function(data){
    if(!data.success) {
      Screenful.status(Screenful.Loc.flaggingFailed, "warn"); //"failed to flag entry"
    } else {
      Screenful.status(Screenful.Loc.ready);
      var $entry=$("div.entry[data-id=\""+entryID+"\"]");
      if($entry.length>0){
        $entry.find(".entryFlagLink").css("background-color", flag.color)
        //if the entry is currently open in the editor, abandon it and reload it there:
        if(window.frames["editframe"].Screenful && window.frames["editframe"].Screenful.Editor && window.frames["editframe"].Screenful.Editor.entryID==entryID) {
          window.frames["editframe"].Screenful.Editor.needsSaving=false;
          window.frames["editframe"].Screenful.Editor.open(e, entryID);
        }
      }
    }
  });


  },

};
$(window).ready(Screenful.Navigator.start);
