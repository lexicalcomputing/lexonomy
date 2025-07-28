class ConfigurationCheckerClass {
   constructor(){
      observable(this)
      this.store = window.store
      this.store.on("dictionaryChanged", this.checkAll.bind(this))
      this.schema = this.store.schema
      this.issues = []
      this.configs = {
         ident: {
            name: "Basic settings",
            url: "ident"
         },
         structure: {
            name: "Structure",
            url: "structure"
         },
         searchability: {
            name: "Searching",
            url: "searchability"
         },
         titling: {
            name: "Headword list",
            url: "titling"
         },
         formatting: {
            name: "Formatting",
            url: "formatting"
         },
         flagging: {
            name: "Flags",
            url: "flagging"
         },
         ske: {
            name: "Sketch Engine",
            url: "ske"
         },
         dict_settings: {
            name: "Admin",
            url: "admin"
         },
         editing: {
            name: "Custom entry editor",
            url: "editing"
         },
         gapi: {
            name: "Multimedia API",
            url: "gapi"
         },
         publico: {
            name: "Publish",
            url: "publico"
         },
         styles: {
            name: "Custom styles",
            url: "styles"
         }
      }
   }

   getAllIssues(){
      return this.issues
   }

   getIssues(configId){
      return this.issues.filter(issue => issue.configId == configId)
   }

   checkAll(){
      let order = ["error", "warning", "info"]
      let issues = Object.keys(this.configs)
            .map(configId => this.checkConfiguration(configId))
            .flat()
            .map(issue => {
               let configdDef = this.configs[issue[0]]
               return {
                  severity: issue[1],
                  message: issue[2],
                  configId: issue[0],
                  configName: configdDef.name,
                  configUrl: configdDef.url
               }
            })
            .sort((a, b) => {
               if(a.severity == b.severity){
                  return a.configName.localeCompare(b.configName)
               }
               return order.indexOf(a.severity) - order.indexOf(b.severity)
            })
      if(!window.objectEquals(this.issues, issues)){
         this.issues = issues
         this.trigger("issuesChanged")
      }
   }

   getIssuesSummary(issues){
      issues = issues || this.issues
      let errorCount = issues.filter(issue => issue.severity == "error").length
      let warningCount = issues.filter(issue => issue.severity == "warning").length
      let errorTooltip = ""
      let warningTooltip = ""
      if(warningCount){
         warningTooltip = `${warningCount} ${warningCount == 1 ? 'warning' : 'warnings'} `
      }
      if(errorCount){
         errorTooltip = `${errorCount} ${errorCount == 1 ? 'error' : 'errors'} `
      }
      if(errorCount || warningCount){
         return `${errorTooltip}${errorCount && warningCount ? ' and ' : ''}${warningTooltip} found in configuration.`
      }
      return ""
   }

   getSeverityColor(issue){
      if(issue){
         return {
            error: "red",
            warning: "orange",
            info: "blue"
         }[issue.severity] || ""
      }
      return ""
   }

   checkConfiguration(configId){
      let checkFunction = this[`check_${configId}`]
      if(typeof checkFunction == "function"){
         return checkFunction.call(this)
      }
      return []
   }

   check_ident(){
      let ident = this.store.data.config.ident
      let result =[]
      if(!ident.title){
         result.push(["ident", "error", `Missing dictionary name.`])
      }
      if(!ident.blurb){
         result.push(["ident", "info", `Dictionary description is empty.`])
      }
      return result
   }

   check_titling(){
      let titling = this.store.data.config.titling
      let result = []
      if(titling){
         if(titling.headword && !this.isElementInStructure(titling.headword)){
            result.push(["titling", "error", `Headword element "${titling.headword}" not found in entry structure.`])
         }
         if(titling.headwordSorting && !this.isElementInStructure(titling.headwordSorting)){
            result.push(["titling", "error", `Headword sorting element "${titling.headwordSorting}" not found in entry structure.`])
         }
         if(titling.headwordAnnotationType == "simple" && this.isNonEmptyArray(titling.headwordAnnotations)){
            titling.headwordAnnotations.forEach(elementPath => {
               if(!this.isElementInStructure(elementPath)){
                  result.push(["titling", "warning", `Headword annotation element "${elementPath}" not found in entry structure.`])
               }
            })
         }
         if(titling.headwordAnnotationsType == "advanced"){
            let regex = /%\((.*?)\)/g
            if(!regex.test(titling.headwordAnnotationsAdvanced)){
               result.push(["titling", "warning", "Headword annotation template does not contain %(ELEMENT)."])
            } else{
               titling.headwordAnnotationsAdvanced.match(regex)
                     .map(x => x.slice(2, -1))
                     .forEach(elementPath => {
                        if(!this.isElementInStructure(elementPath)){
                           result.push(["titling", "error", `Element "${elementPath}" in Headword annotation template not found in entry structre.`])
                        }
                     })
            }
         }
      }
      return result
   }

   check_searchability(){
      let searchability = this.store.data.config.searchability
      let result = []
      if(searchability){
         if(this.isNonEmptyArray(searchability.searchElements)){
            searchability.searchElements.forEach(elementPath => {
               if(!this.isElementInStructure(elementPath)){
                  result.push(["searchability", "warning", `Searchable element "${elementPath}" not found in entry structure.`])
               }
            })
         }
         if(this.isNonEmptyArray(searchability.templates)){
            searchability.templates.forEach(searchTemplate => {
               let error = ""
               try{
                  this.store.advancedSearchParseQuery(searchTemplate.template)
               } catch(e){
                  error = e
               }
               if(error){
                  result.push(["searchability", "error", `Search template "${searchTemplate.label}: ${searchTemplate.template}" is not valid: "${error}".`])
               }
               if(searchTemplate.template.toLowerCase().indexOf("%query%") == -1){
                  result.push(["searchability", "warning", `Search template "${searchTemplate.label}: ${searchTemplate.template}" does not contain string "%query%".`])
               }
            })
         }
      }
      return result
   }

   check_ske(){
      let ske = this.store.data.config.ske
      let result = []
      if(ske){
         if(ske.concquery){
            let regex = /%\((.*?)\)/g
            if(!regex.test(ske.concquery)){
               result.push(["ske", "warning", `Concordance query does not contain %(ELEMENT).`])
            }
            let match = ske.concquery.match(regex)
            match && match.map(x => x.slice(2, -1))
                  .forEach(elementPath => {
                     if(!this.isElementInStructure(elementPath)){
                        result.push(["ske", "error", `Element "${elementPath}" in Concordance query not found in entry structre.`])
                     }
               })
         }

         if(ske.collocationContainer && !this.isElementInStructure(ske.collocationContainer)){
            result.push(["ske", "error", `Collocation container "${ske.collocationContainer}" not found in entry structure.`])
         }
         if(ske.definitionContainer && !this.isElementInStructure(ske.definitionContainer)){
            result.push(["ske", "error", `Definition container "${ske.definitionContainer}" not found in entry structure.`])
         }
         if(this.isNonEmptyArray(ske.searchElements)){
            ske.searchElements.forEach(elementPath => {
               if(!this.isElementInStructure(elementPath)){
                  result.push(["ske", "warning", `Additional search element "${elementPath}" not found in entry structure.`])
               }
            })
         }
         if(ske.exampleContainer && !this.isElementInStructure(ske.exampleContainer)){
            result.push(["ske", "error", `Example container "${ske.exampleContainer}" not found in entry structure.`])
         }
         if(ske.thesaurusContainer && !this.isElementInStructure(ske.thesaurusContainer)){
            result.push(["ske", "error", `Thesaurus container "${ske.thesaurusContainer}" not found in entry structure.`])
         }
      }
      return result
   }

   check_structure(){
      let structure = this.store.data.config.structure
      let result = []
      if(!structure || this.store.schema.isEmpty()){
         result.push(["structure", "error", `Missing structure definition.`])
      } else {
         if(this.store.schema.error){
            result.push(["structure", "error", store.schema.error])
         }
      }
      return result
   }

   check_formatting(){
      let formatting = this.store.data.config.formatting
      let result = []
      if(!formatting?.layout?.desktop?.schema){
         result.push(["formatting", "warning", `You have not defined your entry layout. A simple layout has been automatically created and applied.`])
      } else {
         // TODO check layout, structure, usage only elements from structure
      }
      return result
   }

   check_flagging(){
      let flagging = this.store.data.config.flagging
      let result = []
      if(flagging?.flag_element){
         if(!this.isElementInStructure(flagging.flag_element)){
            result.push(["flagging", "error", `Flag element "${flagging.flag_element}" not found in entry structure.`])
         }
         let flags = flagging.flags
         if(this.isNonEmptyArray(flags)){
            if(flags.filter(flag => !flag.key).length){
               result.push(["flagging", "warning", `Flag keyboard shortcut is empty.`])
            }
            if(flags.filter(flag => !flag.label).length){
               result.push(["flagging", "error", `Flag label must not be empty.`])
            }
            if(flags.filter(flag => !flag.name).length){
               result.push(["flagging", "error", `Flag value must not be empty.`])
            }
            let values = flags.map(flag => flag.name)
            if(values.length != (new Set(values)).size){
               result.push(["flagging", "error", `Each flag must have a unique value.`])
            }
            let colors = flags.map(flag => flag.color)
            if(colors.length != (new Set(colors)).size){
               result.push(["flagging", "info", `Two or more flags have the same color.`])
            }
            let labels = flags.map(flag => flag.label)
            if(labels.length != (new Set(labels)).size){
               result.push(["flagging", "info", `Two or more flags have the same label.`])
            }
            if(flagging.all_additive_key){
               if(flags.find(flag => flag.key == flagging.all_additive_key)){
                  result.push(["flagging", "error", `Keyboard shortcut for adding all additive flags should be different from flag keyboard shortcuts.`])
               }
               if(!flagging.all_additive_label){
                  result.push(["flagging", "info", `Missing Label for adding all additive flags keyboard shortcut.`])
               }
            }

         }
      }
      return result
   }


   isElementInStructure(elementPath){
      return this.schema.getElementByPath(elementPath)
            || window.nvhStore.isServiceElement(elementPath)
   }

   isNonEmptyArray(object){
      return object && object.length
   }
}

window.configurationChecker = new ConfigurationCheckerClass()
