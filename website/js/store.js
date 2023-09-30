class StoreClass {
   constructor(){
      observable(this);

      this.data = {
         isSiteconfigLoading: false,
         isDictionaryListLoading: false,
         isDictionaryListLoaded: false,
         siteconfig: null,
         dictionaryList: [],
         isPublicDictionaryListLoaded: false,
         isPublicDictionaryListLoading: false,
         publicDictionaryList: [],
         entryRevisions: [],
         isEntryRevisionsLoading: false,
         isEntryRevisionsLoaded: false
      }

      this.resetDictionary()
   }

   migrateConfigStructure(structure){
      Object.values(structure.elements).forEach(el => {
         if(el.filling && !el.type){
            el.type = el.filling
            delete el.filling
         }
      })
   }

   getDictionary(dictId){
      return this.data.dictionaryList.find(d => d.id == dictId)
   }

   open(dictId, doctype, entryId, mode){
      this.changeDictionary(dictId)
      this.changeDoctype(doctype)
      entryId && this.changeEntryId(entryId)
      if(mode){
         this.data.mode = mode
      }
   }

   changeDictionary(dictId){
      if(dictId != this.data.dictId){
         this.resetDictionary()
         this.data.dictId = dictId
         window.dictId = dictId  // global variable dictId is used by some custom editors
         if(dictId){
            this.loadActualDictionary()
         } else {
            this.trigger("dictionaryChanged")
         }
      }
   }

   changeDoctype(doctype){
      if(this.data.isDictionaryLoading){
         this.one("dictionaryChanged", this.changeDoctype.bind(this, doctype))
      } else {
         doctype = doctype || this.data.doctypes[0]
         if(doctype != this.data.doctype){
            this.data.doctype = doctype
            this.data.config.structure.root = doctype
            this.trigger("doctypeChanged")
         }
      }
   }

   changeSearchParams(searchParams){
      if(this.data.isDictionaryLoading){
         this.one("dictionaryChanged", this.changeSearchParams.bind(this, searchParams))
      } else {
         let searchtext = searchParams.searchtext || ""
         let modifier = searchParams.modifier || "start"
         if(searchtext !== this.data.searchtext || modifier !== this.data.modifier){
            this.data.searchtext = searchtext
            this.data.modifier = modifier
            this.loadEntryList()
         }
      }
   }

   changeEntryId(entryId){
      if(this.data.isDictionaryLoading){
         this.one("dictionaryChanged", this.changeEntryId.bind(this, entryId))
      } else {
         if(entryId != this.data.entryId){
            this.data.entryId = entryId
            this.loadEntry()
            this.trigger("entryIdChanged")
         }
      }
   }

   searchEntryList(){
      this.loadEntryList()
      url.setQuery(this.data.searchtext ? {
         s: this.data.searchtext,
         m: this.data.modifier
      } : {}, true)
   }

   setEntryFlag(entryId, flag){
      let entry = this.data.entryList.find(e => e.id == entryId)
      entry.isSaving = true
      this.trigger("entryListChanged", entryId)
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/entryflag.json`,
         method: 'POST',
         data: {
            id: entryId,
            flag: flag
         }
      })
            .done(function(flag, response) {
               if(response.success){
                  entry.flag = [flag]
               }
            }.bind(this, flag))
            .fail(response => {
                  M.toast({html: "Flag was not saved."})
            })
            .always(response => {
               delete entry.isSaving
               this.trigger("entryListChanged", entryId)
            })
   }

   getFlag(flagName){
      if(flagName){
         return this.data.config.flagging.flags.find(f => f.name == flagName)
      }
      return null
   }

   getFlagLabel(flagName){
      let flag = this.getFlag(flagName)
      return flag ? flag.label : ""
   }

   getFlagColor(flagName){
      let flag = this.getFlag(flagName)
      return flag ? flag.color : ""
   }

   getFlagTextColor(flagColor){
      let tmp = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(flagColor);
      if(tmp){
         let red = parseInt(tmp[1], 16)
         let green = parseInt(tmp[2], 16)
         let blue = parseInt(tmp[3], 16)
         return (red * 0.299 + green * 0.587 + blue * 0.114) > 186 ? "#000000" : "#ffffff"
      }
      return "#000000"
   }

   resetDictionary(){
      Object.assign(this.data, {
         isDictionaryLoading: false,
         isDictionaryLoaded: false,
         isEntryListLoading: false,
         isEntryListLoaded: false,
         isEntryLoading: false,
         isEntryLoaded: false,
         isDictionaryExamplesLoading: false,
         config: null,
         doctype: null,
         doctypes: null,
         entryList: null,
         entry: null,
         dictId: null,
         entryId: null,
         searchtext: '',
         modifier: 'start',
         mode: 'view',
         userAccess: {
            canView: false,
            canEdit: false,
            canConfig: false,
            canUpload: false,
            canDownload: false
         },
         dictionaryExamples: null,
         dictionaryExamplesHasMore: null
      })
   }

   loadSiteconfig(){
      this.data.isSiteconfigLoading = true
      return $.ajax({url: `${window.API_URL}siteconfigread.json`})
            .done(response => {
               this.data.siteconfig = response
               this.trigger("siteconfigChanged")
            })
            .fail(response => {
               M.toast({html: "Could not load app configuration."})
            })
            .always(response => {
               this.data.isSiteconfigLoading = false
            })
   }

   loadDictionaryList(){
      if(this.data.isDictionaryListLoading){
         return
      }
      this.data.isDictionaryListLoading = true
      this.trigger("dictionaryListLoadingChanged")
      return $.ajax(`${window.API_URL}userdicts.json`)
            .done(response => {
               this.data.dictionaryList = response.dicts || []
               this.data.dictionaryList.sort((a, b) => a.title.localeCompare(b.title, undefined, {numeric: true}))
               this.data.dictionaryList.forEach(d => {
                  if(!d.owners.includes(window.auth.data.email)){
                     d.shared = true
                  }
               })
               this.data.isDictionaryListLoaded = true
               this.trigger("dictionaryListChanged")
            })
            .fail(response => {
               M.toast({html: "Dictionary list could not be loaded."})
            })
            .always(response => {
               this.data.isDictionaryListLoading = false
               this.trigger("dictionaryListLoadingChanged")
            })
   }

   loadPublicDictionaryList(){
      this.data.isPublicDictionaryListLoading = true
      this.trigger("isPublicDictionaryListLoadingChanged")
      return $.ajax(`${window.API_URL}publicdicts.json`)
            .done(response => {
               this.data.isPublicDictionaryListLoaded = true
               this.data.publicDictionaryList = response.entries || []
               this.data.publicDictionaryLanguageList = [...new Set(this.data.publicDictionaryList.map(d => d.lang))].filter(l => !!l)
               if(this.data.isDictionaryListLoaded){
                  let favouriteIds = this.data.dictionaryList.filter(d => d.favorite).map(d => d.id)
                  this.data.publicDictionaryList.forEach(d => {
                     if(favouriteIds.includes(d.id)){
                        d.favorite = true
                     }
                  })
               }
            })
            .fail(response => {
               M.toast({html: "Dictionary list could not be loaded."})
            })
            .always(response => {
               this.data.isPublicDictionaryListLoading = false
               this.trigger("isPublicDictionaryListLoadingChanged")
            })
   }

   loadActualDictionary(){
      if(!this.data.dictId || this.data.isDictionaryLoading){
         return
      }
      this.data.isDictionaryLoading = true
      this.data.isDictionaryLoaded = false
      this.trigger("isDictionaryLoadingChanged")
      this.loadDictionary(this.data.dictId)
            .done(response => {
               if(response.success){
                  // TODO: backward compatibility, may be removed in future
                  //response.configs.structure = response.configs.structure || response.configs.xema
                  for(let elementName in response.configs.structure.elements){
                     response.configs.structure.elements[elementName].children.forEach(c => {
                        c.min = c.min * 1
                        c.max = c.max * 1
                     })
                  }
                  Object.assign(this.data, {
                        config: response.configs,
                        userAccess: response.userAccess,
                        dictConfigs: response.configs,
                        doctype: response.doctype,
                        doctypes: response.doctypes
                     },
                     response.publicInfo
                  )

                  // TODO just temporary, remove after data migration
                  this.migrateConfigStructure(this.data.config.structure)
                  window.xema = this.data.config.structure  // global variable xema is used by some custom editors
                  this.data.isDictionaryLoaded = true
                  this.data.isDictionaryLoading = false
                  this.trigger("dictionaryChanged")
                  this.loadEntryList()
               } else {
                  this.data.isDictionaryLoading = false
                  route("#/")
               }
            })
            .fail(response => {
               this.data.isDictionaryLoading = false
               route("#/")
            })
            .always(response => {
               this.trigger("isDictionaryLoadingChanged")
            })
   }

   loadDictionary(dictId){
      return $.ajax(`${window.API_URL}${dictId}/config.json`)
            .done(response => {
               !response.success && M.toast({html: `Could not load ${dictId} dictionary.`})
            })
            .fail(function(response) {
               M.toast({html: `Could not load ${dictId} dictionary.`})
            }.bind(this, dictId))
   }

   loadEntryList(howmany){
      let authorized = window.auth.data.authorized
      if(!this.data.dictId || (authorized && !this.data.doctype)){
         return
      }
      this.data.isEntryListLoading = true
      this.trigger("entryListLoadingChanged")
      let url;
      let data = {
         searchtext: this.data.searchtext,
         modifier: this.data.modifier,
         howmany: howmany ? howmany : (this.data.dictConfigs.titling.numberEntries || 1000)
      }
      if(authorized && (this.data.userAccess.canView || this.data.userAccess.canEdit)){
         url = `${window.API_URL}${this.data.dictId}/${this.data.doctype}/entrylist.json`
      } else {
         url = `${window.API_URL}${this.data.dictId}/search.json`
      }
      return $.ajax({
         url: url,
         method: "POST",
         data: data
      })
            .done(response => {
               if(response.entries){
                  this.data.entryList = response.entries
                  this.data.entryCount = response.total
               } else {
                  this.data.entryList = []
                  this.data.entryCount = 0
               }
               this.data.isEntryListLoaded = true
               this.trigger("entryListChanged")
            })
            .fail(response => {
               M.toast({html: "Entry list could not be loaded."})
            })
            .always(response => {
               this.data.isEntryListLoading = false
               this.trigger("entryListLoadingChanged")
            })
   }

   loadEntry(){
      if(!this.data.entryId || this.data.entryId == "new"){
         return
      }
      this.data.isEntryLoading = true
      this.trigger("isEntryLoadingChanged")
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/entryread.json`,
         method: "POST",
         data: {
            id: this.data.entryId
         }
      })
            .done(response => {
               this.data.entry = response
               if(this.data.entry.json){
                  this.data.entry.json = JSON.parse(this.data.entry.json)
               }
               this.data.entryRevisions = []
               this.data.isEntryRevisionsLoaded = false
               this.data.isEntryLoaded = true
               this.trigger("entryChanged")
            })
            .fail(response => {
               M.toast({html: "Entry could not be loaded."})
            })
            .always(() => {
               this.data.isEntryLoading = false
               this.trigger("isEntryLoadingChanged")
            })
   }

   createEntry(nvh){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/entrycreate.json`,
         method: "POST",
         data: {
               nvh: nvh
         }
      }).done(response => {
         this.data.entryId = response.id
         this.loadEntryList()
      })
   }

   updateEntry(nvh){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/entryupdate.json`,
         method: "POST",
         data: {
               id: this.data.entryId,
               nvh: nvh
         }
      })
            .done(response => {
               if(this.data.entryRevisions.length){
                  this.loadEntryRevisions()
               }
            })
   }

   deleteEntry(){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/entrydelete.json`,
         method: "POST",
         data: {
               id: this.data.entryId
         }
      }).done(response => {
         if(response.success){
            this.data.entryId = null
            this.data.entryList = this.data.entryList.filter(e => e.id != response.id)
            this.trigger("entryListChanged", response.id)
         }
      })
   }

   loadEntryRevisions(){
      if(!this.data.isEntryRevisionsLoading){
         this.data.isEntryRevisionsLoading = true
         this.trigger("isEntryRevisionsLoadingChanged")
         return $.ajax({
            url: `${window.API_URL}${this.data.dictId}/history.json`,
            method: "POST",
            data: {
                  id: this.data.entryId
            }
         })
               .done(response => {
                  this.data.entryRevisions = response.history
                  this.data.entryRevisions.forEach((r, idx) => {r.idx = idx})
                  this.data.isEntryRevisionsLoaded = true
                  this.trigger("entryRevisionChanged")
               })
               .fail(response => {
                  M.toast({html: "Revisions could not be loaded."})
               })
               .always(response => {
                  this.data.isEntryRevisionsLoading = false
                  this.trigger("isEntryRevisionsLoadingChanged")
               })
      }
   }

   loadEntryLinks(){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/entrylinks.json`,
         data: {
            id: this.data.entryId
         }
      })
            .fail(response => {
               M.toast({html: "Links could not be loaded."})
            })
   }

   createEntryLink(source_el, target_dict, target_id, target_el){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/links/add`,
         data: {
            source_el: source_el,
            source_id: this.data.entryId,
            target_dict: target_dict,
            target_id: target_id,
            target_el: target_el
         }
      })
            .done(response => {
               M.toast({html: "Link created."})
            })
            .fail(response => {
               M.toast({html: "Could not create link."})
            })
   }

   deleteEntryLink(linkId){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/links/delete/${linkId}`
      })
            .fail(response => {
               M.toast({html: "Link deleted."})
            })
            .fail(response => {
               M.toast({html: "Link could not be deleted."})
            })
   }

   loadLinkables(dictId){
       return $.ajax({
         url: `${window.API_URL}${dictId}/linkablelist.json`
      })
   }

   loadDictionaryLinks(){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/links.json`
      })
            .fail(response => {
               M.toast({html: "Dictionary links could not be loaded."})
            })
   }

   loadSchemas(){
      return $.ajax({
         url: `${window.API_URL}schemaitems.json`
      })
            .fail(response => {
               M.toast({html: "Could not load schema templates."})
            })
   }

   loadFinalSchema(schemaItems){
      return $.ajax({
         url: `${window.API_URL}schemafinal.json`,
         method: "POST",
         data: {
            schema_items: JSON.stringify(schemaItems)
         }
      })
            .fail(response => {
               M.toast({html: "Could not load final schema."})
            })
   }

   loadDictionaryConfig(configId){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/configread.json`,
         method: "POST",
         data: {
            id: configId
         }
      })
            .done(response => {
               if(response.id == "structure"){
                  this.migrateConfigStructure(response.content)
               }
            })
            .fail(response => {
               M.toast({html: `Could not load the data ('${configId}'): ${response.statusText}`})
            })
            .always(response => {

            })
   }

   updateDictionaryConfig(configId, data){
      if(configId == "publico"){
         // it may affect publicDictionaryList, load it next time it is needed
         this.data.isPublicDictionaryListLoaded = false
         this.data.publicDictionaryList = []
      }
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/configupdate.json`,
         method: 'POST',
         data: {
            id: configId,
            content: JSON.stringify(data)
         }
      })
            .done(response => {
               this.loadActualDictionary()
               M.toast({html: "Saved"})
            })
            .fail(response => {
               M.toast({html: `Could not save the data ('${configId}'): ${response.statusText}`})
            })
            .always(response => {})
   }

   importDictionaryConfiguration(data){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/importconfigs.json`,
         method: 'POST',
         data: data,
         processData: false,
         contentType: false
      })
            .done(() => {
               this.loadActualDictionary()
               M.toast({html: "Configuration was imoported."})
            })
            .fail(payload => {
               M.toast({html: "Could not import configuration."})
            })
   }

   createDictionary(data){
      return $.ajax({
         url: `${window.API_URL}make.json`,
         method: 'POST',
         data: data
      })
            .done(response => {
               if (response.success) {
                  this.loadDictionaryList()
               }
            })
            .fail(response => {
               M.toast({html: "Could not create dictionary."})
            })
            .always(repsonse => {

            })
   }

   cloneDictionary(dictId){
      return $.ajax({
         url: `${window.API_URL}${dictId}/clone.json`,
         method: 'POST'
      })
            .done(response => {
               this.data.dictionaryList = response.dicts
               M.toast({html: "Dictionary was cloned."})
               this.trigger("dictionaryListChanged")
               this.changeDictionary(response.dictID)
               this.one("dictionaryChanged", () => {
                  route(response.dictID)
               })
            })
            .fail(response => {
               M.toast({html: "Dictionary clone creation failed."})
            })
            .always(repsonse => {
            })
   }

   deleteDictionary(dictId){
      return $.ajax({
         url: `${window.API_URL}${dictId}/destroy.json`,
         method: 'POST'
      })
            .done(response => {
               this.data.dictionaryList = response.dicts
               // TODO merge with loadDictionaryList data processing
               this.data.dictionaryList.sort((a, b) => a.title.localeCompare(b.title, undefined, {numeric: true}))
               this.data.dictionaryList.forEach(d => {
                  if(!d.owners.includes(window.auth.data.email)){
                     d.shared = true
                  }
               })
               M.toast({html: "Dictionary was deleted."})
               this.trigger("dictionaryListChanged")
            })
            .fail(response => {
               M.toast({html: "Dictionary clone creation failed."})
            })
            .always(repsonse => {

            })
   }

   toggleDictionaryFavorite(dictId, favorite){
      this.setDictionaryAttribute(dictId, "isSaving", true)
      this.trigger("favoriteChanged")
      return $.ajax({
            url: `${window.API_URL}changefavdict.json`,
            method: 'POST',
            data: {
               dictId: dictId,
               status: favorite
            }
         })
               .done(function(dictId, response) {
                  this.setDictionaryAttribute(dictId, "favorite", favorite)
                  if(favorite && !this.getDictionary(dictId)){
                     // if user add public dictionary to the favorite list, we need to reload
                     // user dictionary list - it contains favorite dictionaries
                     this.loadDictionaryList()
                  }
               }.bind(this, dictId))
               .fail(response => {
               })
               .always(() => {
                  this.setDictionaryAttribute(dictId, "isSaving", false)
                  this.trigger("favoriteChanged")
               })
   }

   loadAdminDictionaryList(searchtext, howmany){
      return $.ajax({
            url: `${window.API_URL}dicts/dictlist.json`,
            method: "POST",
            data: {
               searchtext: searchtext || "",
               howmany: howmany || 100
            }
         })
            .fail(response => {
               M.toast({html: "Dictionary list could not be loaded."})
            })
   }

   loadAdminUserList(searchtext, howmany){
      return $.ajax({
            url: `${window.API_URL}users/userlist.json`,
            method: "POST",
            data: {
               searchtext: searchtext || "",
               howmany: howmany || 100
            }
         })
            .fail(response => {
               M.toast({html: "User list could not be loaded."})
            })
   }

   createUser(email){
      return $.ajax({
         url: `${window.API_URL}users/usercreate.json`,
         method: 'POST',
         data: {
            id: email
         }
      })
            .done(response => {
               M.toast({html: "User was created."})
            })
            .fail(response => {
               M.toast({html: "User could not be created."})
            })
   }

   deleteUser(email){
      return $.ajax({
         url: `${window.API_URL}users/userdelete.json`,
         method: 'POST',
         data: {
            id: email
         }
      })
            .done(response => {
               M.toast({html: "User was deleted."})
            })
            .fail(response => {
               M.toast({html: "User could not be deleted."})
            })
            .always(repsonse => {
            })
   }

   setDictionaryAttribute(dictId, attrName, attrValue){
      let dictionary = this.getDictionary(dictId)
      if(dictionary){
         dictionary[attrName] = attrValue
      }
   }

   uploadXML(data){
      return $.ajax({
            url: `${window.API_URL}${this.data.dictId}/upload.html`,
            method: 'POST',
            data: data,
            processData: false,
            contentType: false
         })
   }

   importXML(data){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/import.json`,
         data: data
      })
            .done(response => {
               if(response.finished){
                  this.loadDictionaryList()
                  this.loadEntryList()
               }
            })
   }

   reloadDictionaryExamples(){
      if(!this.data.dictId || this.data.isDictionaryExamplesLoading){
         return
      }
      this.data.isDictionaryExamplesLoading = true
      this.trigger("isDictionaryExamplesLoading")
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/random.json`,
         method: 'POST'
      })
            .done(response => {
               this.data.dictionaryExamples = response.entries
               this.data.dictionaryExamplesHasMore = response.more
               this.trigger("dictionaryExamplesChanged")
            })
            .fail(response => {
               M.toast({html: "Could not load the examples."})
            })
            .always(response => {
               this.data.isDictionaryExamplesLoading = false
               this.trigger("isDictionaryExamplesLoading")
            })
   }

   skeLoadCorpora(){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/skeget/corpora`
      })
            .fail(response => {
               M.toast({html: "Could not load Sketch Engine corpora."})
            })
   }

   skeLoadData(method, data){
      //$.get("/"+dictId+"/skeget/xampl/", {url: kex.apiurl, corpus: kex.corpus, username: ske_username, apikey: ske_apiKey, querytype: querytype, query: query, fromp: fromp}, function(json){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/skeget/${method}`,
         data: data
      })
            .fail(response => {
               M.toast({html: "Could not load Sketch Engine data."})
            })
   }

   loadKontextCorpora(){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/kontext/corpora`
      })
            .fail(response => {
               M.toast({html: "Could not load Kontext corpora."})
            })
   }

   suggestUrl(){
      return $.ajax({
         url: `${window.API_URL}makesuggest.json`
      })
            .fail(response => {
               M.toast({html: "Could not generate URL of the new dictionary."})
            })
   }

   autoAddImages(addElem, addNumber){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/autoimage.json`,
         method: 'POST',
         data: {
            "addElem": addElem,
            "addNumber": addNumber
         }
      })
            .fail(response => {
               M.toast({html: "Could not automatically add images."})
            })
   }

   autoAddImagesGetProgress(jobId){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/autoimageprogress.json`,
         data: {jobid: jobId}
      })
            .fail(response => {
               M.toast({html: "Could not check image generation progress."})
            })

   }

   startLinking(otherDictID){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/linknaisc.json`,
         data: {otherdictID: otherDictID}
      })
            .fail(response => {
               M.toast({html: "Could not initiate linking process."})
            })
   }

   linkingCheckIfRunning(){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/linking.json`
      })
            .fail(response => {
               M.toast({html: "Could not check linking process."})
            })
   }

   linkingGetProgress(otherDictID, jobID){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/naiscprogress.json`,
         data: {
            otherdictID: otherDictID,
            jobid: jobID
         }
      })
            .fail(response => {
               M.toast({html: "Could not check the linking progress."})
            })
   }

   autonumberElements(countElem, storeElem){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/autonumber.json`,
         method: 'POST',
         data: {
            "countElem": countElem,
            "storeElem": storeElem
         }
      })
            .fail(response => {
               M.toast({html: "Autonumbering failed."})
            })
   }

   sendFeedback(email, text){
      return $.ajax({
            url: `${window.API_URL}feedback.json`,
            method: "POST",
            data: {
               email: email,
               text: text
            }
         })
            .fail(response => {
               M.toast({html: "Could not send the feedback."})
            })
   }
}

window.store = new StoreClass()
