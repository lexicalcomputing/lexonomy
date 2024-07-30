class StoreClass {
   constructor(){
      observable(this);
      this.const = {
         QUERY_OPERATORS: [            // true/false - can be used with "Any element" option
            ["is", "=", "is equal to", true],
            ["is_not", "!=", "is not equal to", true],
            ["regex", "~=", "match regular expression", true],
            ["contains", "~=", "contains", true],
            ["starts_with", "~=", "starts with", true],
            ["ends_with", "~=", "ends with", true],
            ["count_is", "#=", "count is", false],
            ["count_more", "#>", "count is more than", false],
            ["count_less", "#<", "count is less than", false],
            ["exists", "#>", "exists", false],
            ["not_exists", "#<", "not exists", false]
         ],
         ENTRY_TYPES: {
            string: "Text",
            markup: "Text markup",
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
      } else if(this.data.config){  // is dictionary loaded
         doctype = doctype || this.data.doctypes[0]
         if(doctype != this.data.doctype){
            this.data.doctype = doctype
            this.data.config.structure.root = doctype
            this.trigger("doctypeChanged")
         }
      }
   }

   changeSearchParams(searchParams){
      let newSearchParams = {
         tab: searchParams.tab || this.data.search.tab,
         searchtext: searchParams.searchtext || "",
         modifier: searchParams.modifier || "start",
         advanced_query: searchParams.advanced_query || ""
      }
      if(JSON.stringify(this.data.search) != JSON.stringify(newSearchParams)){
         Object.assign(this.data.search, newSearchParams)
         this.trigger("searchParamsChanged")
         if(!this.data.isDictionaryLoading){
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
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/entryflag.json`,
         data: {
            id: entryId,
            flag: flag
         }
      })
            .done(function(flag, response) {
               if(response.success){
                  entry.flag = [flag]
                  if(entry.id == this.data.entryId){
                     // TODO: does not work in source code tab
                     this._setElementValue(element => element.name == this.data.config.flagging.flag_element, flag)
                  }
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
         userAccess: false,
         dictionaryExamples: null,
         dictionaryExamplesHasMore: null
      })
   }

   loadSiteconfig(){
      this.data.isSiteconfigLoading = true
      return window.connection.get({url: `${window.API_URL}siteconfigread.json`})
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
      return window.connection.get(`${window.API_URL}userdicts.json`)
            .done(response => {
               if(response.dicts){
                  this._setDictionaryList(response.dicts)
                  this.data.isDictionaryListLoaded = true
               }
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
      return window.connection.get(`${window.API_URL}publicdicts.json`)
            .done(response => {
               if(response.success){
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
                  // TODO just temporary fix until backend is be updated
                  if(!response.userAccess && response.publicInfo && response.publicInfo.public){
                     response.userAccess = {canView: true}
                  }
                  if(!response.userAccess){
                     this.trigger("unauthorizedDictionary")
                     return
                  }
                  let elements = response.configs.structure.elements
                  if(!response.configs.formatting){
                     response.configs.formatting = {
                        elements: response.configs.xemplate
                     }
                  }
                  if(!response.configs.formatting.elements){
                     response.configs.formatting = {elements: response.configs.formatting}
                  }
                  if(!response.configs.searchability.templates){
                     response.configs.searchability.templates = []
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
                     // TODO configs and dictConfigs?
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
                  this.data.search.modifier = localStorage.getItem("entryFilterModifier") || "substring"
                  this.loadEntryList()
                  window.CustomStyles.add("customDictionaryStyle", this.data.config.styles.css)
               }
            })
            .always(response => {
               this.data.isDictionaryLoading = false
               this.trigger("isDictionaryLoadingChanged")
               if(response.userAccess && !["dict-config-structure", "unauthorized"].includes(this.data.actualPage)
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
      return window.connection.get(`${window.API_URL}${dictId}/config.json`)
            .done(response => {
               !response.success && M.toast({html: `Could not load ${dictId || 'the'} dictionary.`})
            })
            .fail(function(response) {
               M.toast({html: `Could not load ${dictId || 'the'} dictionary.`})
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
      return window.connection.post({
         url: url,
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
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/entryread.json`,
         data: {
            id: this.data.entryId
         }
      })
            .done(response => {
               if(response.success){
                  this.data.entry = response
                  this.data.entryRevisions = []
                  this.data.isEntryRevisionsLoaded = false
                  this.data.isEntryLoaded = true
                  this.trigger("entryChanged")
               }
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
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/entrycreate.json`,
         data: {
            nvh: nvh
         }
      })
            .done(response => {
               if(response.success){
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
               }
            })
   }

   updateEntry(nvh){
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/entryupdate.json`,
         data: {
            id: this.data.entryId,
            nvh: nvh
         }
      })
            .done(response => {
               if(response.success){
                  this.data.entry.nvh = response.content
                  if(this.data.entryRevisions.length){
                     this.loadEntryRevisions()
                  }
                  this.updateFlagInEntryList(nvh)
               }
            })
   }

   deleteEntry(){
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/entrydelete.json`,
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
         return window.connection.post({
            url: `${window.API_URL}${this.data.dictId}/history.json`,
            data: {
                  id: this.data.entryId
            }
         })
               .done(response => {
                  if(response.history){
                     this.data.entryRevisions = response.history
                     this.data.entryRevisions.forEach((r, idx) => {r.idx = idx})
                     this.data.isEntryRevisionsLoaded = true
                     this.trigger("entryRevisionChanged")
                  }
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
      return window.connection.get({
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
      return window.connection.get({
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
               if(response.success){
                  M.toast({html: "Link created."})
               }
            })
            .fail(response => {
               M.toast({html: "Could not create link."})
            })
   }

   deleteEntryLink(linkId){
      return window.connection.get({
         url: `${window.API_URL}${this.data.dictId}/links/delete/${linkId}`
      })
            .done(response => {
               if(response.success){
                  M.toast({html: "Link deleted."})
               }
            })
            .fail(response => {
               M.toast({html: "Link could not be deleted."})
            })
   }

   loadLinkables(dictId){
       return window.connection.get({
         url: `${window.API_URL}${dictId}/linkablelist.json`
      })
   }

   loadDictionaryLinks(){
      return window.connection.get({
         url: `${window.API_URL}${this.data.dictId}/links.json`
      })
            .fail(response => {
               M.toast({html: "Dictionary links could not be loaded."})
            })
   }

   loadSchemas(){
      return window.connection.get({
         url: `${window.API_URL}schemaitems.json`
      })
            .fail(response => {
               M.toast({html: "Could not load schema templates."})
            })
   }

   loadFinalSchema(schemaItems){
      return window.connection.post({
         url: `${window.API_URL}schemafinal.json`,
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
      return window.connection.post({
         url: `${window.API_URL}schema_to_json.json`,
         data: {
            schema: JSON.stringify(schema)
         }
      })
            .fail(response => {
               M.toast({html: "Could not transform schema to JSON format."})
            })
   }

   loadDictionaryConfig(configId){
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/configread.json`,
         data: {
            id: configId
         }
      })
            .done(response => {
               if(response.success){
                  if(response.id == "structure"){
                     this.migrateConfigStructure(response.content)
                  }
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
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/dictconfigupdate.json`,
         data: {
            id: configId,
            content: JSON.stringify(data)
         }
      })
            .done(response => {
               if(response.success){
                  this.loadActualDictionary()
                  M.toast({html: "Saved"})
               }
            })
            .fail(response => {
               M.toast({html: `Could not save the data ('${configId}'): ${response.statusText}`})
            })
            .always(response => {})
   }

   updateDictionaryAccess(users){
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/dictaccessupdate.json`,
         data: {
            users: JSON.stringify(users)
         }
      })
            .done(response => {
               if(response.success){
                  this.loadActualDictionary()
                  M.toast({html: "Saved"})
               }
            })
            .fail(response => {
               M.toast({html: `Could not save the data ('users'): ${response.statusText}`})
            })
            .always(response => {})
   }

   updateDictionarySettings(data){
      // only for admins
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/dictsettingsupdate.json`,
         data: {
            configs: JSON.stringify(data)
         }
      })
            .done(response => {
               if(response.success){
                  this.loadActualDictionary()
                  M.toast({html: "Saved"})
               }
            })
            .fail(response => {
               M.toast({html: `Could not save the settings: ${response.statusText}`})
            })
            .always(response => {})
   }

   changeDictionaryUrl(url){
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/move.json`,
         data: {
            url: url
         }
      })
            .done(response => {
               if(response.success){
                  M.toast({html: "Dictionary URL has been changed."})
               } else {
                  M.toast({html: "Could not change the dictionary URL."})
               }
            })
   }

   isDictIdTaken(dictId){
      return window.connection.get(`${window.API_URL}${dictId}/config.json`)
   }

   importDictionaryConfiguration(data){
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/importconfigs.json`,
         data: data,
         processData: false,
         contentType: false
      })
            .done(response => {
               if(response.success){
                  this.loadActualDictionary()
                  M.toast({html: "Configuration was imoported."})
               }
            })
            .fail(payload => {
               M.toast({html: "Could not import configuration."})
            })
   }

   isDictionaryUrlTaken(url){
      return window.connection.post({
         url: `${window.API_URL}exists.json`,
         data: {
            url: url
         }
      })
            .fail(payload => {
               M.toast({html: "Could not check dictionary URL."})
            })
   }

   createDictionary(data, xhrParams={}){
      return window.connection.post(Object.assign({
         url: `${window.API_URL}make.json`,
         method: 'POST',
         data: data
      }, xhrParams))
            .done(response => {
               if(response.success) {
                  this.loadDictionaryList()
                  M.toast({html: "Dictionary was created."})
               }
            })
            .fail(response => {
               M.toast({html: "Could not create dictionary."})
            })
   }

   cloneDictionary(dictId){
      return window.connection.post({
         url: `${window.API_URL}${dictId}/clone.json`
      })
            .done(response => {
               if(response.success){
                  this._setDictionaryList(response.dicts)
                  M.toast({html: "Dictionary was cloned."})
                  this.changeDictionary(response.dictID)
                  this.one("dictionaryChanged", () => {
                     route(response.dictID)
                  })
               }
            })
            .fail(response => {
               M.toast({html: "Dictionary clone creation failed."})
            })
            .always(response => {
            })
   }

   deleteDictionary(dictId){
      return window.connection.post({
         url: `${window.API_URL}${dictId}/destroy.json`,
      })
            .done(response => {
               if(response.success){
                  this._setDictionaryList(response.dicts)
                  M.toast({html: "Dictionary was deleted."})
               }
            })
            .fail(response => {
               M.toast({html: "Could not delete the dictionary."})
            })
            .always(response => {

            })
   }

   toggleDictionaryFavorite(dictId, favorite){
      this.setDictionaryAttribute(dictId, "isSaving", true)
      this.trigger("favoriteChanged")
      return window.connection.post({
            url: `${window.API_URL}changefavdict.json`,
            data: {
               dictId: dictId,
               status: favorite
            }
         })
               .done(function(dictId, response) {
                  if(response.success){
                     this.setDictionaryAttribute(dictId, "favorite", favorite)
                     if(favorite && !this.getDictionary(dictId)){
                        // if user add public dictionary to the favorite list, we need to reload
                        // user dictionary list - it contains favorite dictionaries
                        this.loadDictionaryList()
                     }
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
      return window.connection.post({
            url: `${window.API_URL}dicts/dictlist.json`,
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
      return window.connection.post({
            url: `${window.API_URL}users/userlist.json`,
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
      return window.connection.post({
         url: `${window.API_URL}users/usercreate.json`,
         data: {
            id: email,
            manager: isManager
         }
      })
            .done(response => {
               if(response.success){
                  M.toast({html: "User was created."})
               }
            })
            .fail(response => {
               M.toast({html: "User could not be created."})
            })
   }

   loadUsers(searchtext, howmany){
      return window.connection.post({
         url: `${window.API_URL}users/userlist.json`,
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
      return window.connection.post({
         url: `${window.API_URL}users/userread.json`,
         data: {
            id: email
         }
      })
   }

   deleteUser(email){
      return window.connection.post({
         url: `${window.API_URL}users/userdelete.json`,
         data: {
            id: email
         }
      })
            .done(response => {
               if(response.success){
                  M.toast({html: "User was deleted."})
               }
            })
            .fail(response => {
               M.toast({html: "User could not be deleted."})
            })
            .always(response => {
            })
   }

   changeSketchEngineUsername(ske_username){
      return window.connection.post({
         url: `${window.API_URL}changeskeusername.json`,
         data: {
            ske_userName: ske_username
         }
      })
            .done(response => {
               if(response.success){
                  M.toast({html: "Sketch Engine username was changed."})
               }
            })
            .fail(response => {
               M.toast({html: "Sketch Engine username could not be changed."})
            })
   }

   changeSketchEngineApiKey(ske_apiKey){
      return window.connection.post({
         url: `${window.API_URL}changeskeapi.json`,
         data: {
            ske_apiKey: ske_apiKey
         }
      })
            .done(response => {
               if(response.success){
                  M.toast({html: "Sketch Engine API key was changed."})
               }
            })
            .fail(response => {
               M.toast({html: "Sketch Engine API key could not be changed."})
            })
   }

   changePassword(password){
      return window.connection.post({
         url: `${window.API_URL}changepwd.json`,
         data: {
            ske_apiKey: ske_apiKey
         }
      })
            .done(response => {
               if(response.success){
                  M.toast({html: "Password was changed."})
               }
            })
            .fail(response => {
               M.toast({html: "Password could not be changed."})
            })
   }

   changeLexonomyApiKey(apiKey){
      return window.connection.post({
         url: `${window.API_URL}changeoneclickapi.json`,
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



   _setElementValue(elementSelector, value){
      // used to update element value changed in DB otherwise than in NVH editor
      // updates: element value in this.data.entry.nvh (entry in NVH format, string)
      //        : element in nvhStore.data.entry (entry in JSON format)
      let nvhStore = window.nvhStore
      let nvhStoreElement = nvhStore.findElement(elementSelector)
      if(nvhStoreElement){
         nvhStoreElement.value = value
         let jsonEntry = nvhStore.nvhToJson(this.data.entry.nvh)
         let element = nvhStore.findElement(elementSelector, jsonEntry)
         if(element){
            element.value = value
            this.data.entry.nvh = nvhStore.jsonToNvh(jsonEntry)
            nvhStore.trigger("updateElements", [nvhStoreElement])
         }
      }
   }

   setDictionaryAttribute(dictId, attrName, attrValue){
      let dictionary = this.getDictionary(dictId)
      if(dictionary){
         dictionary[attrName] = attrValue
      }
   }

   importFile(data){
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/import.json`,
         data: data,
         processData: false,
         contentType: false
      })
   }

   checkImportProgress(upload_file_path){
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/getImportProgress.json`,
         data: {upload_file_path: upload_file_path}
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
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/random.json`,
      })
            .done(response => {
               if(response.entries){
                  this.data.dictionaryExamples = response.entries
                  this.data.dictionaryExamplesHasMore = response.more
                  this.trigger("dictionaryExamplesChanged")
               }
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
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/randomone.json`
      })
            .done(response => {
               if(response.success){
                  this.data.entryId = response.id
                  this.data.entry = response
                  this.data.entryRevisions = []
                  this.data.isEntryRevisionsLoaded = false
                  this.data.isEntryLoaded = true
                  this.trigger("entryIdChanged")
                  this.trigger("entryChanged")
               }
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
      return window.connection.get({
         url: `${window.API_URL}projects/list.json`
      })
            .fail(response => {
               M.toast({html: "Could not load projects."})
            })
   }

   loadProject(projectID){
      return window.connection.get({
         url: `${window.API_URL}projects/${projectID}/project.json`
      })
   }

   createProject(project){
      return window.connection.post({
         url: `${window.API_URL}projects/create.json`,
         data: project
      })
            .done(response => {
               if(response.error){
                  M.toast({html: `Could not create the project: ${response.error}`})
               } else if(response.success) {
                  M.toast({html: "Project was created."})
               }
            })
            .fail(response => {
               M.toast({html: "Could not create the project."})
            })
   }

   updateProject(project){
      return window.connection.post({
         url: `${window.API_URL}projects/${project.id}/update.json`,
         data: project
      })
            .done(response => {
               if(response.success){
                  M.toast({html: "Project was updated."})
               }
            })
            .fail(response => {
               M.toast({html: "Could not update the project."})
            })
   }

   archiveProject(projectID){
      return window.connection.post({
         url: `${window.API_URL}projects/${projectID}/archive.json`
      })
            .done(response => {
               if(response.success){
                  M.toast({html: "Project was archived."})
               }
            })
            .fail(response => {
               M.toast({html: "Could not archive the project."})
            })
   }

   unarchiveProject(projectID){
      return window.connection.post({
         url: `${window.API_URL}projects/${projectID}/unarchive.json`
      })
            .done(response => {
               if(response.success){
                  M.toast({html: "Project was unarchived."})
               }
            })
            .fail(response => {
               M.toast({html: "Could not unarchive the project."})
            })
   }

   deleteProject(projectID){
      return window.connection.post({
         url: `${window.API_URL}projects/${projectID}/delete.json`
      })
            .done(response => {
               if(response.success){
                  M.toast({html: "Project was deleted."})
               }
            })
            .fail(response => {
               M.toast({html: "Could not delete the project."})
            })
   }

   loadWorkflows(){
      return window.connection.get({
         url: `${window.API_URL}wokflows/list.json`
      })
            .fail(response => {
               M.toast({html: "Could not load list of workflows."})
            })
   }

   projectExportBatches(projectID, stage, size, count){
      return window.connection.post({
         url: `${window.API_URL}projects/${projectID}/create_batch.json`,
         data: {
            stage: stage,
            size: size,
            batch_number: count,
         }
      })
            .done(response => {
               if(response.success){
                  M.toast({html: "Batches were created."})
               }
            })
            .fail(response => {
               M.toast({html: "Could not create batches."})
            })
   }

   projectAssignBatch(projectID, assignees){
      return window.connection.post({
         url: `${window.API_URL}projects/${projectID}/assign_batch.json`,
         data: {
            assignees: JSON.stringify(assignees)
         }
      })
            .done(response => {
               if(response.error){
                  M.toast({html: "Could not assign editor to the batch."})
               } else {
                  M.toast({html: "Editor was asigned to the batch."})
               }
            })
   }

   projectAcceptBatches(projectID, dictID_list){
      return window.connection.post({
         url: `${window.API_URL}projects/${projectID}/accept_batch.json`,
         data: {
            dictID_list: JSON.stringify(dictID_list)
         }
      })
            .done(response => {
               if(response.error){
                  M.toast({html: "Could not accept the batch."})
               } else {
                  M.toast({html: "Batch was accepted."})
               }
            })
   }

   projectRejectBatches(projectID, dictID_list){
      return window.connection.post({
         url: `${window.API_URL}projects/${projectID}/reject_batch.json`,
         data: {
            dictID_list: JSON.stringify(dictID_list)
         }
      })
            .done(response => {
               if(response.error){
                  M.toast({html: "Could not reject the batch."})
               } else {
                  M.toast({html: "Batch was rejected."})
               }
            })
   }

   projectImportAcceptedBatches(projectID, stage){
      return window.connection.post({
         url: `${window.API_URL}projects/${projectID}/make_stage.json`,
         data: {
            stage: stage
         }
      })
            .done(response => {
               if(response.success){
                  M.toast({html: "Batches were improted."})
               }
            })
            .fail(response => {
               M.toast({html: "Could not import batches."})
            })
   }

   skeLoadCorpora(){
      return window.connection.get({
         url: `${window.API_URL}user_corpora.json`
      })
            .fail(response => {
               M.toast({html: "Could not load Sketch Engine corpora."})
            })
   }

   skeLoadData(method, data){
      //$.get("/"+dictId+"/skeget/xampl/", {url: kex.apiurl, corpus: kex.corpus, username: ske_username, apikey: ske_apiKey, querytype: querytype, query: query, fromp: fromp}, function(json){
      return window.connection.get({
         url: `${window.API_URL}${this.data.dictId}/skeget/${method}`,
         data: data
      })
            .fail(response => {
               M.toast({html: "Could not load Sketch Engine data."})
            })
   }

   loadKontextCorpora(){
      return window.connection.get({
         url: `${window.API_URL}${this.data.dictId}/kontext/corpora`
      })
            .fail(response => {
               M.toast({html: "Could not load Kontext corpora."})
            })
   }

   suggestUrl(){
      return window.connection.get({
         url: `${window.API_URL}makesuggest.json`
      })
            .fail(response => {
               M.toast({html: "Could not generate URL of the new dictionary."})
            })
   }

   autoAddImages(addElem, addNumber){
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/autoimage.json`,
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
      return window.connection.get({
         url: `${window.API_URL}${this.data.dictId}/autoimageprogress.json`,
         data: {jobid: jobId}
      })
            .fail(response => {
               M.toast({html: "Could not check image generation progress."})
            })

   }

   autonumberElements(countElem, storeElem){
      return window.connection.post({
         url: `${window.API_URL}${this.data.dictId}/autonumber.json`,
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
      return window.connection.post({
            url: `${window.API_URL}feedback.json`,
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

   updateFlagInEntryList(nvh){
      let flagging = this.data.config.flagging
      if(flagging){
         let entry = window.nvhStore.nvhToJson(nvh)
         let flagElement = window.nvhStore.findElement(e => e.name == flagging.flag_element, entry)
         if(flagElement){
            let listItem = this.data.entryList.find(e => e.id == this.data.entryId)
            if(listItem && listItem.flag != flagElement.value){
               listItem.flag = [flagElement.value]
               this.trigger("entryListChanged", this.data.entryId)
            }
         }
      }
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
         } else if(this.data.search.modifier.startsWith("template_")){
            if(this.data.search.searchtext){
               let templateLabel = this.data.search.modifier.split("template_")[1]
               let template = this.data.config.searchability.templates.find(t => t.label.toLowerCase() == templateLabel)
               if(template){
                  template = template.template.replaceAll("%query%", this.data.search.searchtext)
                  data.advance_query = template
               } else {
                  M.toast({html: "Search template not found."})
               }
            }
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
      if(rule.attr != ".*" && !this.data.config.structure.elements[rule.attr]){
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
