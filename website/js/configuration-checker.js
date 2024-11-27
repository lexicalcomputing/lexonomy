class ConfigurationCheckerClass {
   constructor(){
      observable(this)
      this.store = window.store
      this.store.on("dictionaryChanged", this.checkAll.bind(this))
      this.issues = []
      this.configs = {
         dict_settings: {
            name: "Sketch Engine",
            url: "admin"
         },
         editing: {
            name: "Custom entry editor",
            url: "editing"
         },
         flagging: {
            name: "Flags",
            url: "flagging"
         },
         formatting: {
            name: "Formatting",
            url: "formatting"
         },
         gapi: {
            name: "Multimedia API",
            url: "gapi"
         },
         ident: {
            name: "Basic settings",
            url: "ident"
         },
         links: {
            name: "Linking",
            url: "links"
         },
         publico: {
            name: "Publishing",
            url: "publico"
         },
         searchability: {
            name: "Searching",
            url: "searchability"
         },
         ske: {
            name: "Sketch Engine",
            url: "ske"
         },
         structure: {
            name: "Structure",
            url: "structure"
         },
         styles: {
            name: "Custom styles",
            url: "styles"
         },
         titling: {
            name: "Headword list",
            url: "titling"
         }
      }
   }

   getAllIssues(){
      return this.issues
   }

   getIssues(configId){
      return this.issues.filter(issue => issue.configId == configId)
   }

   checkAll(config){
      config = config || window.store.data.config
      let order = ["error", "warning", "info"]
      let issues = Object.keys(this.configs)
            .map(configId => this.checkConfiguration(configId, config))
            .flat()
            .map(issue => {
               let config = this.configs[issue[0]]
               return {
                  severity: issue[1],
                  message: issue[2],
                  configId: issue[0],
                  configName: config.name,
                  configUrl: config.url
               }
            })
            .sort((a, b) => {
               if(a.severity == b.severity){
                  return a.configName.localeCompare(b.configNamen)
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

   checkConfiguration(configId, config){
      config = config || window.store.data.config
      let checkFunction = this[`check_${configId}`]
      if(typeof checkFunction == "function"){
         return checkFunction.call(this, config)
      }
      return []
   }

   check_ident(config){
      let result =[]
      if(!config.ident.title){
         result.push(["ident", "error", `Missing dictionary name.`])
      }
      if(!config.ident.blurb){
         result.push(["ident", "info", `Dictionary description is empty.`])
      }
      return result
   }

   check_titling(config){
      let result = []
      if(config.titling){
         if(config.titling.headword && !this.isElementInStructure(config.titling.headword, config)){
            result.push(["titling", "error", `Headword element "${config.titling.headword}" not found in entry structure.`])
         }
         if(config.titling.headwordSorting && !this.isElementInStructure(config.titling.headwordSorting, config)){
            result.push(["titling", "error", `Headword sorting element "${config.titling.headwordSorting}" not found in entry structure.`])
         }
         if(config.titling.headwordAnnotationType == "simple" && this.isNonEmptyArray(config.titling.headwordAnnotations)){
            config.titling.headwordAnnotations.forEach(elementPath => {
               if(!this.isElementInStructure(elementPath, config)){
                  result.push(["titling", "warning", `Headword annotation element "${elementPath}" not found in entry structure.`])
               }
            })
         }
         if(config.titling.headwordAnnotationsType == "advanced"){
            let regex = /%\((.*?)\)/g
            if(!regex.test(config.titling.headwordAnnotationsAdvanced)){
               result.push(["titling", "warning", "Headword annotation template does not contain %(ELEMENT)."])
            } else{
               config.titling.headwordAnnotationsAdvanced.match(regex)
                     .map(x => x.slice(2, -1))
                     .forEach(elementPath => {
                        if(!this.isElementInStructure(elementPath, config)){
                           result.push(["titling", "error", `Element "${elementPath}" in Headword annotation template not found in entry structre.`])
                        }
                     })
            }
         }
      }
      return result
   }

   check_searchability(config){
      let result = []
      if(config.searchability){
         if(this.isNonEmptyArray(config.searchability.searchElements)){
            config.searchability.searchElements.forEach(elementPath => {
               if(!this.isElementInStructure(elementPath, config)){
                  result.push(["searchability", "warning", `Searchable element "${elementPath}" not found in entry structure.`])
               }
            })
         }
         if(this.isNonEmptyArray(config.searchability.templates)){
            config.searchability.templates.forEach(searchTemplate => {
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

   check_links(config){
      let result = []
      if(config.links){
         Object.entries(config.links).forEach(([linkingElement, elementConfig]) => {
            if(!this.isElementInStructure(linkingElement, config)){
               result.push(["links", "warning", `Linking element "${linkingElement}" not found in entry structure.`])
            }
            if(!elementConfig.identifier){
               result.push(["links", "error", `Missing Identifier for Linking element "${linkingElement}".`])
            } else {
               let regex = /%\((.*?)\)/g
               if(!regex.test(elementConfig.identifier)){
                     result.push(["links", "warning", `Idenitifer for Linking element "${linkingElement}" does not contain %(ELEMENT).`])
                  } else{
                     elementConfig.identifier.match(regex)
                           .map(x => x.slice(2, -1))
                           .forEach(elementPath => {
                              if(!this.isElementInStructure(elementPath, config)){
                                 result.push(["links", "error", `Element "${elementPath}" in Identifier field for Linking element "${linkingElement}" not found in entry structre.`])
                              }
                           })
                  }
            }
         })
      }
      return result
   }

   check_ske(config){
      let result = []
      if(config.ske){
         if(config.ske.concquery){
            let regex = /%\((.*?)\)/g
            if(!regex.test(config.ske.concquery)){
               result.push(["ske", "warning", `Concordance query does not contain %(ELEMENT).`])
            }
            let match = config.ske.concquery.match(regex)
            match && match.map(x => x.slice(2, -1))
                  .forEach(elementPath => {
                     if(!this.isElementInStructure(elementPath, config)){
                        result.push(["ske", "error", `Element "${elementPath}" in Concordance query not found in entry structre.`])
                     }
               })
         }

         if(config.ske.collocationContainer && !this.isElementInStructure(config.ske.collocationContainer, config)){
            result.push(["ske", "error", `Collocation container "${config.ske.collocationContainer}" not found in entry structure.`])
         }
         if(config.ske.definitionContainer && !this.isElementInStructure(config.ske.definitionContainer, config)){
            result.push(["ske", "error", `Definition container "${config.ske.definitionContainer}" not found in entry structure.`])
         }
         if(this.isNonEmptyArray(config.ske.searchElements)){
            config.ske.searchElements.forEach(elementPath => {
               if(!this.isElementInStructure(elementPath, config)){
                  result.push(["ske", "warning", `Additional search element "${elementPath}" not found in entry structure.`])
               }
            })
         }
         if(config.ske.exampleContainer && !this.isElementInStructure(config.ske.exampleContainer, config)){
            result.push(["ske", "error", `Example container "${config.ske.exampleContainer}" not found in entry structure.`])
         }
         if(config.ske.thesaurusContainer && !this.isElementInStructure(config.ske.thesaurusContainer, config)){
            result.push(["ske", "error", `Thesaurus container "${config.ske.thesaurusContainer}" not found in entry structure.`])
         }
      }
      return result
   }

   check_structure(config){
      let result = []
      if(!config.structure){
         result.push(["structure", "error", `Missing structure definition.`])
      } else {
         if(!config.structure.root){
            result.push(["structure", "error", `Root element is not defined in entry structure.`])
         } else if(!this.isElementInStructure(config.structure.root, config)){
            result.push(["structure", "error", `Root element not found in structure definition.`])
         }
         if(!config.structure.elements){
            result.push(["structure", "error", `No element defined in entry structure.`])
         }
      }
      return result
   }

   check_flagging(config){
      let result = []
      if(config.flagging.flag_element){
         if(!this.isElementInStructure(config.flagging.flag_element, config)){
            result.push(["flagging", "error", `Flag element "${config.flagging.flag_element}" not found in entry structure.`])
         }
         let flags = config.flagging.flags
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
            if(config.flagging.all_additive_key){
               if(flags.find(flag => flag.key == config.flagging.all_additive_key)){
                  result.push(["flagging", "error", `Keyboard shortcut for adding all additive flags should be different from flag keyboard shortcuts.`])
               }
               if(!config.flagging.all_additive_label){
                  result.push(["flagging", "info", `Missing Label for adding all additive flags keyboard shortcut.`])
               }
            }

         }
      }
      return result
   }


   isElementInStructure(elementPath, config){
      return (config.structure && config.structure.elements && !!config.structure.elements[elementPath])
            || window.nvhStore.isServiceElement(elementPath)
   }

   isNonEmptyArray(object){
      return object && object.length
   }
}

window.configurationChecker = new ConfigurationCheckerClass()
