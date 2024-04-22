class StoreClass {
   constructor(){
      observable(this);
      this.const = {
         QUERY_OPERATORS: [
            ["is", "=", "is equal to"],
            ["is_not", "!=", "is not equal to"],
            ["regex", "~=", "match regular expression"],
            ["contains", "~=", "contains"],
            ["starts_with", "~=", "starts with"],
            ["ends_with", "~=", "ends with"],
            ["count_is", "#=", "count is"],
            ["count_more", "#>", "count is more than"],
            ["count_less", "#<", "count is less than"],
            ["exists", "#>", "exists"],
            ["not_exists", "#<", "not exists"]
         ],
         ENTRY_TYPES: {
            string: "Text",
            int: "Number",
            image: "Image",
            audio: "Audio",
            url: "URL",
            empty: "Empty", // no value, just child elements
            bool: "Yes/No",
            list: "List"
         }
      }
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
         isEntryRevisionsLoaded: false,
         actualPage: null,
         search: {
            tab: localStorage.getItem("entryFilterTab") || "basic",
            searchtext: '',
            modifier: 'start',
            advanced_query: ''
         }
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

   open(dictId, doctype, entryId, editorMode){
      this.changeDictionary(dictId)
      this.changeDoctype(doctype)
      entryId && this.changeEntryId(entryId)
      if(editorMode){
         this.data.editorMode = editorMode
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
      Object.assign(this.data.search, {
         tab: searchParams.tab || this.data.search.tab,
         searchtext: searchParams.searchtext || "",
         modifier: searchParams.modifier || "start",
         advanced_query: searchParams.advanced_query || ""
      })
      this.trigger("searchParamsChanged")
      if(!this.data.isDictionaryLoading){
         this.loadEntryList()
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

   updateURLSearchQuery(){
      if(this.data.search.tab == "advanced"){
         url.setQuery(this.data.search.advanced_query ? {
            t: "advanced",
            q: this.data.search.advanced_query
         } : {}, true)
      } else if(this.data.search.tab == "basic"){
         url.setQuery(this.data.search.searchtext ? {
            t: "basic",
            s: this.data.search.searchtext,
            m: this.data.search.modifier
         } : {}, true)
      }
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

   getLanguageCode(name){
      let lang = this.data.siteconfig.langs.find(l => l.lang == name)
      if(lang){
         return lang.code
      }
      return ""
   }

   getLanguageName(code){
      let lang = this.data.siteconfig.langs.find(l => l.code == code)
      if(lang){
         return lang.lang
      }
      return ""
   }

   getElementDisplayedName(elementName){
      let formatting = this.data.config.formatting.elements
      if(formatting && formatting[elementName] && formatting[elementName].name){
         return formatting[elementName].name
      }
      return elementName
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

   isStructureValid(){
      return this.data.config
            && this.data.config.structure
            && this.data.config.structure.root
            && this.data.config.structure.elements
            && Object.values(this.data.config.structure.elements).every(element => {
               return element.children
                     && element.type
                     && this.const.ENTRY_TYPES[element.type]
            })
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
         search: {
            tab: this.data.search.tab,
            searchtext: '',
            modifier: 'start',
            advanced_query: ''
         },
         editorMode: 'view',
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
               this._setDictionaryList(response.dicts)
               this.data.isDictionaryListLoaded = true
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
      window.CustomStyles.remove("customDictionaryStyle")
      this.trigger("isDictionaryLoadingChanged")
      this.loadDictionary(this.data.dictId)
            .done(response => {
               if(response.success){
                  let elements = response.configs.structure.elements
                  if(!response.configs.formatting){
                     response.configs.formatting = {
                        elements: response.configs.xemplate
                     }
                  }
                  if(!response.configs.formatting.elements){
                     response.configs.formatting.elements = {}
                  }
                  if(elements){
                     Object.keys(elements).forEach(elementName => {
                        if(!response.configs.formatting.elements[elementName]){
                           response.configs.formatting.elements[elementName] = {}
                        }
                     })
                     Object.values(elements).forEach(element => {
                        if(typeof element.children == "undefined"){
                           element.children = []
                        }
                        if(typeof element.min != "undefined"){
                           element.min = element.min * 1
                        }
                        if(typeof element.max != "undefined"){
                           element.max = element.max * 1
                        }
                        element.values = element.values || []
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
                  document.title = `Lexonomy - ${this.data.title}`
                  this.trigger("dictionaryChanged")
                  this.loadEntryList()
                  window.CustomStyles.add("customDictionaryStyle", this.data.config.styles.css)
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
               if(!["dict-config-structure", "unauthorized"].includes(this.data.actualPage)
                     && (!this.data.doctypes
                              || !this.data.doctypes.length
                              || !this.data.doctypes[0]
                              || !this.isStructureValid()
                        )
               ){
                  this.showBrokenStructureDialog()
               }
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

   loadMoreEntries(){
      if(!this.data.isLoadingMoreEntries && (this.data.entryCount > this.data.entryList.length)){
         this.data.isLoadingMoreEntries = true
         this.trigger("isLoadingMoreEntriesChanged")
         this.loadEntries(this.getEntrySearchParams(null, this.data.entryList.length))
               .done(response => {
                  if(response.entries){
                     this.data.entryList = this.data.entryList.concat(response.entries)
                     this.data.entryCount = response.total
                  }
               })
               .always(response => {
                  this.data.isLoadingMoreEntries = false
                  this.trigger("isLoadingMoreEntriesChanged")
               })
      }
   }

   loadEntryList(howmany){
      if(!this.data.dictId || (window.auth.data.authorized && !this.data.doctype)){
         return
      }
      this.data.isEntryListLoading = true
      this.trigger("isEntryListLoadingChanged")
      return this.loadEntries(this.getEntrySearchParams(howmany))
            .done(response => {
               if(response.entries){
                  this.data.entryList = response.entries
                  this.data.entryCount = response.total
               } else {
                  this.data.entryList = []
                  this.data.entryCount = 0
               }
               this.data.isEntryListLoaded = true
               this.updateURLSearchQuery()
               this.trigger("entryListChanged")
            })
            .always(response => {
               this.data.isEntryListLoading = false
               this.trigger("isEntryListLoadingChanged")
            })
   }

   loadEntries(data){
      let url
      if(window.auth.data.authorized && (this.data.userAccess.canView || this.data.userAccess.canEdit)){
         url = `${window.API_URL}${this.data.dictId}/${this.data.doctype}/entrylist.json`
      } else {
         url = `${window.API_URL}${this.data.dictId}/search.json`
      }
      return $.ajax({
         url: url,
         method: "POST",
         data: data
      })
            .fail(response => {
               M.toast({html: "Entry list could not be loaded."})
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
      })
            .done(response => {
               this.data.entry = {
                  id: response.id,
                  nvh: response.content
               }
               this.data.entryId = response.id
               this.data.entryRevisions = []
               this.data.isEntryRevisionsLoaded = false
               this.data.isEntryLoaded = true
               this.loadEntryList()
               this.trigger("entryChanged")
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
               this.data.entry.nvh = response.content
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
               if(response.statusText != "abort"){
                  M.toast({html: "Could not load final schema."})
               }
            })
   }

   schemaToJSON(schema){
      return $.ajax({
         url: `${window.API_URL}schema_to_json.json`,
         method: "POST",
         data: {
            schema: JSON.stringify(schema)
         }
      })
            .fail(response => {
               M.toast({html: "Could not transform schema to JSON format."})
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
         url: `${window.API_URL}${this.data.dictId}/dictconfigupdate.json`,
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

   updateDictionaryAccess(users){
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/dictaccessupdate.json`,
         method: 'POST',
         data: {
            users: JSON.stringify(users)
         }
      })
            .done(response => {
               this.loadActualDictionary()
               M.toast({html: "Saved"})
            })
            .fail(response => {
               M.toast({html: `Could not save the data ('users'): ${response.statusText}`})
            })
            .always(response => {})
   }

   updateDictionarySettings(data){
      // only for admins
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/dictsettingsupdate.json`,
         method: 'POST',
         data: {
            configs: JSON.stringify(data)
         }
      })
            .done(response => {
               this.loadActualDictionary()
               M.toast({html: "Saved"})
            })
            .fail(response => {
               M.toast({html: `Could not save the settings: ${response.statusText}`})
            })
            .always(response => {})
   }

   isDictIdTaken(dictId){
      return $.ajax(`${window.API_URL}${dictId}/config.json`)
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
                  M.toast({html: "Dictionary was created."})
               }
            })
            .fail(response => {
               M.toast({html: "Could not create dictionary."})
            })
   }

   cloneDictionary(dictId){
      return $.ajax({
         url: `${window.API_URL}${dictId}/clone.json`,
         method: 'POST'
      })
            .done(response => {
               this._setDictionaryList(response.dicts)
               M.toast({html: "Dictionary was cloned."})
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
               this._setDictionaryList(response.dicts)
               M.toast({html: "Dictionary was deleted."})
            })
            .fail(response => {
               M.toast({html: "Could not delete the dictionary."})
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

   _setDictionaryList(dictionaryList){
      this.data.dictionaryList = dictionaryList || []
      this.data.dictionaryList.sort((a, b) => a.title.localeCompare(b.title, undefined, {numeric: true}))
      this.data.dictionaryList.forEach(d => {
         if(!d.owners.includes(window.auth.data.email)){
            d.shared = true
         }
      })
      this.trigger("dictionaryListChanged")
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
               if(response.statusText != "abort"){
                  M.toast({html: "User list could not be loaded."})
               }
            })
   }

   createUser(email, isManager){
      return $.ajax({
         url: `${window.API_URL}users/usercreate.json`,
         method: 'POST',
         data: {
            id: email,
            manager: isManager
         }
      })
            .done(response => {
               M.toast({html: "User was created."})
            })
            .fail(response => {
               M.toast({html: "User could not be created."})
            })
   }

   resetUserPassword(email){
      return $.ajax({
         url: `${window.API_URL}users/userupdate.json`,
         method: 'POST',
         data: {
            email: email
         }
      })
            .done(response => {
               M.toast({html: "User password was reset."})
            })
            .fail(response => {
               M.toast({html: "User password could not be reset."})
            })
   }

   loadUsers(searchtext, howmany){
      return $.ajax({
         url: `${window.API_URL}users/userlist.json`,
         method: 'POST',
         data: {
            searchtext: searchtext,
            howmany: howmany
         }
      })
            .fail(response => {
               if(response.statusText != "abort"){
                  M.toast({html: "Could not load users."})
               }
            })
   }

   getUser(email){
      return $.ajax({
         url: `${window.API_URL}users/userread.json`,
         method: 'POST',
         data: {
            id: email
         }
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

   changeSketchEngineUsername(ske_username){
      return $.ajax({
         url: `${window.API_URL}changeskeusername.json`,
         method: 'POST',
         data: {
            ske_userName: ske_username
         }
      })
            .done(response => {
               M.toast({html: "Sketch Engine username was changed."})
            })
            .fail(response => {
               M.toast({html: "Sketch Engine username could not be changed."})
            })
   }

   changeSketchEngineApiKey(ske_apiKey){
      return $.ajax({
         url: `${window.API_URL}changeskeapi.json`,
         method: 'POST',
         data: {
            ske_apiKey: ske_apiKey
         }
      })
            .done(response => {
               M.toast({html: "Sketch Engine API key was changed."})
            })
            .fail(response => {
               M.toast({html: "Sketch Engine API key could not be changed."})
            })
   }

   changePassword(password){
      return $.ajax({
         url: `${window.API_URL}changepwd.json`,
         method: 'POST',
         data: {
            ske_apiKey: ske_apiKey
         }
      })
            .done(response => {
               M.toast({html: "Password was changed."})
            })
            .fail(response => {
               M.toast({html: "Password could not be changed."})
            })
   }

   changeLexonomyApiKey(apiKey){
      return $.ajax({
         url: `${window.API_URL}changeoneclickapi.json`,
         method: 'POST',
         data: {
            apiKey: apiKey
         }
      })
            .done(response => {
               if(response.success){
                  window.auth.data.apiKey = apiKey
                  if(apiKey){
                     M.toast({html: "API key was changed."})
                  } else {
                     M.toast({html: "API key was removed."})
                  }
               }
            })
            .fail(response => {
               M.toast({html: "API key could not be changed."})
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
      this.trigger("isDictionaryExamplesLoadingChanged")
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
               this.trigger("isDictionaryExamplesLoadingChanged")
            })
   }

   loadRandomEntry(){
      if(!this.data.dictId){
         return
      }
      this.data.isEntryLoading = true
      this.trigger("isEntryLoadingChanged")
      return $.ajax({
         url: `${window.API_URL}${this.data.dictId}/randomone.json`,
         method: 'POST'
      })
            .done(response => {
               this.data.entryId = response.id
               this.data.entry = response
               this.data.entryRevisions = []
               this.data.isEntryRevisionsLoaded = false
               this.data.isEntryLoaded = true
               this.trigger("entryIdChanged")
               this.trigger("entryChanged")
            })
            .fail(response => {
               M.toast({html: "Could not load the example."})
            })
            .always(response => {
               this.data.isEntryLoading = false
               this.trigger("isEntryLoadingChanged")
            })
   }

   loadProjects(){
      return $.ajax({
         url: `${window.API_URL}/projects`
      })
            .fail(response => {
               M.toast({html: "Could not load projects."})
            })
   }

   loadProject(projectID){
      return $.ajax({
         url: `${window.API_URL}/projects/${projectID}`
      })
            .fail(response => {
               M.toast({html: "Could not load the project."})
            })
   }

   createProject(project){
      return $.ajax({
         url: `${window.API_URL}/projects/new`,
         method: "POST",
         data: project
      })
            .done(response => {
               M.toast({html: "Project was created."})
            })
            .fail(response => {
               M.toast({html: "Could not create the project."})
            })
   }

   updateProject(project){
      return $.ajax({
         url: `${window.API_URL}/projects/update`,
         method: "POST",
         data: project
      })
            .done(response => {
               M.toast({html: "Project was updated."})
            })
            .fail(response => {
               M.toast({html: "Could not update the project."})
            })
   }

   skeLoadCorpora(){
      return $.ajax({
         url: `${window.API_URL}/user_corpora.json`
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

   showBrokenStructureDialog(){
      let content = this.data.userAccess.canConfig
            ? `There is an error in dictionary configruation. Entry structure is broken. <div class="center-align mt-6"><a id="btnOpenStructureConfig" class="btn btn-primary">open structure settings</a></div>`
            : `There is an error in dictionary configruation. Entry structure is broken. Please contact the owner of the dictionary`
      window.modal.open({
         title: "Broken structure",
         tag: "raw-html",
         small: true,
         props: {
            content: content
         }
      })
      setTimeout(() => {
         $("#btnOpenStructureConfig").click(()=>{
            window.modal.close();
            route(`${this.data.dictId}/config/structure`)
         })
      }, 400)
   }

   getEntrySearchUrlQueryString(){
      if(this.data.search.tab == "basic"){
         return this.data.search.searchtext ? url.stringifyQuery({
            t: "basic",
            s: this.data.search.searchtext,
            m: this.data.search.modifier
         }) : ""
      } else {
         return this.data.search.advanced_query ? url.stringifyQuery({
            t: "advanced",
            q: this.data.search.advanced_query
         }) : ""
      }
   }

   getEntrySearchParams(howmany, offset){
      let data = {
         howmany: howmany || this.data.dictConfigs.titling.numberEntries || 500,
         offset: offset || 0
      }
      if(this.data.search.tab == "basic"){
         if(this.data.search.searchtext.startsWith("#")){
            data.id = this.data.search.searchtext.substring(1)
         } else if(this.data.search.modifier == "id"){
            data.id = this.data.search.searchtext
         } else {
            data.searchtext = this.data.search.searchtext
            data.modifier = this.data.search.modifier
         }
      } else {
         data.advance_query = this.data.search.advanced_query
      }
      return data
   }

   advancedSearchParseQuery(query){
      let parseGroup = (groupArray) => {
         let children = []
         if(groupArray.includes("and") && groupArray.includes("or")){
            throw `"AND" and "OR" operators should not be on the same level. Please, enclose parts of expression in brackets.`
         }
         let groupItems = groupArray.filter(group => {
            return !["and", "or"].includes(group)
         })
         for(let i = 0; i < groupItems.length; i++){
            let item = groupItems[i]
            if(item != "where"){
               if(i > 0 && groupItems[i - 1] == "where"){
                  if(Array.isArray(item)){
                     children.at(-1).where = parseGroup(item)
                  } else {
                     children.at(-1).where = {
                        type: "group",
                        operator: "and",
                        children: [this.advancedSearchParseRule(item, groupArray)]
                     }
                  }
               } else {
                  if(Array.isArray(item)){
                     children.push(parseGroup(item))
                  } else {
                     children.push(this.advancedSearchParseRule(item, groupArray))
                  }
               }
            }
         }
         return {
            type: "group",
            operator: groupArray.includes("or") ? "or" : "and",
            children: children
         }
      }

      let getQueryParts = (query) => {
         /*
            copy of Lexonomy advance_searach.py get_query_parts()
            example:
            "(a and (b or c)) or d"
               -> result is array:
            [["a","and",["b","or","c"]],"or","d"]
         */
         let stack = [[]]
         let queryParts = []
         this.advancedSearchSplitQuery(query, queryParts)
         queryParts.forEach(part => {
            let right = '(?<right>\\\)*)?'
            if(typeof part == "string" && part.match(new RegExp("[(]"))){
               stack.at(-1).push([])
               stack.push(stack.at(-1).at(-1))
            } else if(typeof part == "string" && part.match(new RegExp("[)]"))){
               stack.pop()
               if(!stack.length){
                  throw "Opening bracket is missing."
               }
            } else {
               stack.at(-1).push(part)
            }
         })
         if(stack.length > 1){
            throw "Closing bracket is missing."
         }
         return stack.pop()
      }

      let queryParts = getQueryParts(query)
      return parseGroup(queryParts)
   }

   advancedSearchStringifyItem(token){
      if(token.children){
         return token.children.filter(t => t.type == "group" || this.advancedSearchIsRuleValid(t))
               .map(t => {
                  let stringifiedGroup = this.advancedSearchStringifyItem(t)
                  if(stringifiedGroup && t.type == "group"){
                     return `(${stringifiedGroup})`
                  } else {
                     return stringifiedGroup
                  }
               })
               .filter(t => t != "")
               .join(` ${token.operator} `)
      } else if(token.type == "rule"){
         let ret = ""
         let operator = this.advancedSearchStringToOperator(token.operator)
         let value = token.value
         if(token.operator == "exists"){
            ret = `${token.attr}#>"0"`
         } if(token.operator == "not_exists"){
            ret = `${token.attr}#="1"`
         } else {
            if(token.operator == "contains"){
               value = `.*${value}.*`
            }
            if(token.operator == "starts_with"){
               value = `^${value}`
            }
            if(token.operator == "ends_with"){
               value = `${value}$`
            }
            ret = `${token.attr}${operator}"${value}"`
         }
         if(token.where){
            let where = token.where.children.filter(t => t.type == "group" || this.advancedSearchIsRuleValid(t))
               .map(t => {
                  let stringifiedGroup = this.advancedSearchStringifyItem(t)
                  if(stringifiedGroup && t.type == "group"){
                     return `(${stringifiedGroup})`
                  } else {
                     return stringifiedGroup
                  }
               })
               .filter(t => t != "")
               .join(` ${token.where.operator} `)
            if(where){
               ret += ` where (${where})`
            }
         }
         return ret
      } else {
         return ""
      }
   }

   advancedSearchParseRule(rule, groupArray){
      if(!this.data.config.structure.elements[rule.attr]){
         let suggestion = Object.keys(this.data.config.structure.elements).find(element =>  element.startsWith(rule.attr))
         throw `Unknown element "${rule.attr}".${suggestion ? ' Did you mean "' + suggestion + '"?' : ''}`
      }
      if(!rule.operator){
         throw `Missing operator for "${rule.attr}".`
      }
      if(!rule.value){
         let missingQuotes = ""
         if(groupArray.length){
            let ruleIdx = groupArray.findIndex(g => g.attr = rule.attr)
            let nextRule = groupArray[ruleIdx + 1]
            if(nextRule && !this.data.config.structure.elements[nextRule.attr]){
               missingQuotes = ` Did you forget to put "${nextRule.attr}" in quotes?`
            }
         }
         throw `Missing value for "${rule.attr}${rule.operator}".${missingQuotes}`
      }
      let operator = this.advancedSearchOperatorToString(rule.operator)
      let value = rule.value || ""
      if(operator == "regex"){
         if(rule.value.match(/^\.\*\w*\.\\*$/)){
            operator = "contains"
            value = rule.value.substr(2, rule.value.length - 2)
         } else if(rule.value.match(/^\^\w*$/)){
            operator = "starts_with"
            value = rule.value.substr(1)
         } else if(rule.value.match(/^\w*\$$/)){
            operator = "ends_with"
            value = rule.value.substr(0, rule.value.length - 1)
         }
      } else if(operator == "count_is" && value == "0"){
         operator = "not_exists"
      } else if(operator == "count_more" && value == "0"){
         operator = "exists"
      }
      return {
         type: "rule",
         attr: rule.attr,
         value: `${value.replaceAll("\"", "\\\"")}`,
         operator: operator
      }
   }

   advancedSearchSplitQuery(query, parts){
      if(query){
         let attr = '(\\\s*(?<attr>((?!=|!=|~=|#=|#>|#<| |\\\(|\\\)).)*)\\\s*)'
         let operators ='(\\\s*(?<operator>=|!=|~=|#=|#>|#<)\\\s*)?'
         let value = '("(?<value>((?!=|!=|~=|#=|#>|#<).)*)")?'
         let and_or = '(\\\s*(?<lop>where|and|or)\\\s*)?'
         let rest = '(?<rest>.*)?'
         let left = '(?<left>\\\(*)?'
         let right = '(?<right>\\\)*)?'
         let querySplitRegex = new RegExp('^' + left + attr + operators + value + right + and_or + rest + '$')

         let groups = querySplitRegex.exec(query).groups
         //left bracket
         if(groups.left){
            groups.left.split("")
                  .forEach(g => parts.push(g))
         }
         //attribute operator value
         let condition = {};
         ['attr', 'operator', 'value'].forEach(i => {
            if(groups[i]){
               condition[i] = groups[i] || null
            }
         })
         parts.push(condition)
         // right bracket
         if(groups.right){
            groups.right.split("")
                  .forEach(g => parts.push(g))
         }
         // and/or operator
         if(groups.lop){
            parts.push(groups.lop)
         }
         // rest
         if(groups.rest){
            groups.rest = groups.rest.trim()
            if(new RegExp('^[()]*$').test(groups.rest)){
               parts.push(groups.rest)
              } else{
               this.advancedSearchSplitQuery(groups.rest, parts)
            }
         }
      }
   }

   advancedSearchIsQueryValid(query){
      try{
         this.advancedSearchParseQuery(query)
         return true
      } catch(e){
         return false
      }
   }

   advancedSearchIsRuleValid(rule){
      return !!rule.attr
            && !!rule.operator
            && typeof rule.value != "undefined"
            && rule.value !== ""
   }

   advancedSearchOperatorToString(operator){
      let o = this.const.QUERY_OPERATORS.find(o => o[1] == operator)
      if(o){
         return o[0]
      }
      throw "Unknown operator " + operator
   }

   advancedSearchStringToOperator(str){
      let o = this.const.QUERY_OPERATORS.find(o => o[0] == str)
      if(o){
         return o[1]
      }
      throw "Unknown operator " + str
   }
}

window.store = new StoreClass()
