class NVHStoreClass {
   constructor(){
      this.const = {
         nvhNewLine: "\\\\n",
         serviceElementPrefix: "__lexonomy__"
      }
      this.data = {
         entry: null,
         // used to store droped items into side panel
         detachedEntry: {
            path: "",
            children: []
         },
         isContextMenuOpen: false,
         isRevisionsOpen: false,
         draggedElement: null,
         rootElement: null,
         collapsedElements: new Set(), //  to collapse same elements after changing the entry
         lastElementId: 0
      }
      observable(this)
      this.schema = window.store.schema
      this.history = new window.HistoryClass()
      this.history.on("stateChange", this.onHistoryStateChange.bind(this))
      window.store.on("dictionaryChanged", this.onDictionaryChanged.bind(this))
      window.store.on("entryIdChanged", this.onEntryIdChanged.bind(this))
      window.store.on("entryChanged", this.onEntryChanged.bind(this))
      this.on("updateElements", this.validateElements.bind(this))
   }

   createNewEntry(){
      window.store.data.entryId = "new"
      this.data.entry = this._getNewEntry()
      this.validateAllElements()
      this.history.reset()
      this.addStateToHistory()
      window.store.data.editorMode == "view" && this.changeEditorMode("edit")
      this.trigger("entryIdChanged")
      this.trigger("entryContentChanged")
      this.updateUrl()
      this.focusFirstElement()
   }

   saveEntry(){
      this.data.isSaving = true
      this.trigger("isSavingChanged")
      if(this.data.customEditor && window.store.data.editorMode != "code"){
         this.setEntryFromCustomEditor()
      }
      let nvh = this.replaceElementPathsWithNames(this.jsonToNvh(this.data.entry))
      if(window.store.data.entryId != "new"){
         return window.store.updateEntry(nvh)
               .always(response => {
                  if(response.success){
                     M.toast({html: "Entry updated"})
                  } else {
                     M.toast({html: `Entry was not updated: ${response.feedback || ""}`})
                  }
                  this.data.isSaving = false
                  this.trigger("isSavingChanged")
                  this.trigger("entryUpdated")
               })
      } else {
         return window.store.createEntry(nvh)
            .always(response => {
               if(response.success){
                  M.toast({html: "Entry created"})
               } else {
                  M.toast({html: `Entry was not created: ${response.feedback}`})
               }
               this.data.isSaving = false
               this.trigger("isSavingChanged")
               this.updateUrl() // change "new" to entryId
            })
      }
   }

   duplicateEntry(){
      window.store.data.entryId = "new"
      this.saveEntry()
            .done(response => {
               window.store.data.entryId = response.id
               this.history.reset()
               this.addStateToHistory()
               this.updateUrl()
               this.focusFirstElement()
            })
   }

   deleteEntry(){
      if(window.store.data.entryId != "new"){
         this.data.isSaving = true
         this.trigger("isSavingChanged")
         return window.store.deleteEntry()
               .always(response => {
                  if(response.success){
                     M.toast({html: "Entry was deleted"})
                     this.data.entry = null
                     this.trigger("entryIdChanged")
                     this.updateUrl()
                  } else {
                     M.toast({html: `Entry was not deleted: ${response.feedback}`})
                  }
                  this.data.isSaving = false
                  this.trigger("isSavingChanged")
               })
      } else{
         this.data.entry = null
         this.trigger("entryIdChanged")
         this.updateUrl()
      }
   }

   toggleCompleted(){
      this.data.isSavingCompleted = true
      this.trigger("isSavingCompletedChanged")
      let completed = !this.isEntryCompleted()
      return window.store.toggleEntryCompleted(completed)
            .always(response => {
               if(response.success){
                  let completedElementPath = `${window.store.schema.getRoot().name}.__lexonomy__complete`
                  this.data.entry.children = this.data.entry.children.filter(child => child.path != completedElementPath)
                  if(completed){
                     let element = this._addChildElement(this.data.entry, completedElementPath)
                     element.value = "1"
                     element.isValid = true
                  }
                  this.addStateToHistory()
                  this.trigger("updateElements", [this.data.entry])
                  this.trigger("entryUpdated")
               }
               this.data.isSavingCompleted = false
               this.trigger("isSavingCompletedChanged")
            })
   }

   saveStyle(){
      return window.connection.post({
         url: `${window.API_URL}${window.store.data.dictId}/dictconfigupdate.json`,
         data: {
            id: "formatting",
            content: JSON.stringify(this.data.formatting)
         },
         failMessage: "Could not update element style."
      })
   }

   onDictionaryChanged(){
      this.data.structure = window.store.data.config.structure
      this.data.formatting = window.store.data.config.formatting
      this.data.editing = window.store.data.config.editing
      this.data.rootElement = this.schema.getRoot()?.path
      this.data.customEditor = null
      this.data.legacyCustomEditor = false
      this.data.collapsedElements.clear()
      if(this.data.editing.useOwnEditor){
         if(window.store.data.editorMode == "view"){
            this.changeEditorMode("edit") // custom editor does not have view mode
         }
         try{
            let customEditor = new Function("return " + this.data.editing.js)();
            if(customEditor.editor && customEditor.harvester){
               this.data.customEditor = customEditor
               this.data.legacyCustomEditor = true
            } else if(customEditor.editor && customEditor.getValue){
               this.data.customEditor = customEditor
            } else{
               M.toast({html: "Invalid custom editor. Methods editor() and getValue() are required."})
            }
         } catch(e){
            M.toast({html: "Invalid custom editor code."})
         }
      }
      this.onEntryChanged()
   }

   onEntryIdChanged(){
      if(!window.store.data.entryId || window.store.data.entryId == "new"){
         this.onEntryChanged()
      }
   }

   onEntryChanged(){
      this.data.storedEntry = null
      this.data.revision = null
      this.history.reset()
      try{
         this.data.brokenEntryNvh = null
         if(window.store.data.entryId){
            if(window.store.data.entryId == "new"){
               this.data.entry = this._getNewEntry()
            } else{
               this.data.entry = this.nvhToJson(window.store.data.entry.nvh)
               this.forEachElement(el => {
                  el.collapsed = this.data.collapsedElements.has(el.path)
               })
            }
            this.validateAllElements()
            this.addStateToHistory()
         } else {
            this.data.entry = null
         }
         this.trigger("entryContentChanged")
      } catch(e){
         this.data.entry = null
         this.data.brokenEntryNvh = window.store.data.entry.nvh
         this.history.addState(window.store.data.entry.nvh)
         if(window.store.data.actualPage == "dict-edit"){
            if(this.getAvailableActions().code){
               if(window.store.data.editorMode == "code"){
                  this.trigger("brokenEntryNvhChanged")
               } else {
                  this.changeEditorMode("code")
               }
               window.showToast(`Entry is not valid, please, fix the entry.\n ${e}`)
            } else {
               window.showToast(`Could not show the entry: ${e}`)
            }
         }
      }
   }

   updateEntryNvh(nvh){
      try{
         this.data.entry = this.nvhToJson(nvh)
         this.data.brokenEntryNvh = null
         this.validateAllElements()
         this.trigger("entryContentChanged")
      } catch (e){
         this.data.entry = null
         this.data.brokenEntryNvh = nvh
         this.trigger("brokenEntryNvhChanged")
      }
   }

   callIfNoNeedToSave(callback, evt) {
      if(window.store.data.actualPage == "dict-edit"
            && (this.data.entryId == "new"
                  || (window.store.data.entry
                           && this.data.entry
                           && this.hasEntryChanged()
                     )
               )
            ){
         let isSaveAvailable = this.getAvailableActions().save
         let buttons = [{
            label: "Return to editing",
            onClick: (dialog, modal) => {
               modal.close()
            }
         }, {
            label: "Discard changes",
            onClick: (dialog, modal) => {
               callback()
               modal.close()
            }
         }]
         if(isSaveAvailable){
            buttons.unshift({
               label: "Save",
               onClick: (dialog, modal) => {
                  modal.close()
                  this.saveEntry()
                  this.one("isSavingChanged", () => {
                     callback()
                  })
               }
            })
         }

         window.modal.open({
            title: "Changes not saved",
            dismissible: false,
            showCloseButton: false,
            centered: true,
            small: true,
            buttons: buttons
         })
      } else {
         callback && callback()
      }
   }

   hasEntryChanged(){
      if(window.store.data.entryId == "new"){
         return true
      } else {
         try{
            return !this.areNvhJsonsEqual(this.data.entry, this.nvhToJson(window.store.data.entry.nvh))
         } catch(e){
            window.showToast(`Entry is invalid: ${e}`)
            return false
         }
      }
   }

   showRevision(revision){
      if(revision){
         if(!this.data.storedEntry){
            this.data.storedEntry = this.data.entry
         }
         this.updateEntryNvh(revision.content)
         this.data.revision = revision
      } else{
         this.data.revision = null
         this.data.entry = this.data.storedEntry
         this.data.storedEntry = null
      }
      this.trigger("revisionChanged")
   }

   restoreRevision(){
      this.data.revision = null
      this.data.storedEntry = null
      this.addStateToHistory()
      this.closeRevisions()
      this.saveEntry()
      this.trigger("entryContentChanged")
   }

   guessNvhIndentSize(nvh){
      const DEFAULT_INDENT = 2
      let indentLevels = nvh.split('\n')
               .map(line => line.replaceAll("\t", "  "))
               .filter(line => line.trim() != "")
               .map(line => line.match(/^ */)[0].length)
      if(!indentLevels.length){
         return DEFAULT_INDENT
      }
      // Calculate differences between consecutive indent levels
      let diffCounts = {}
      for (let i = 1; i < indentLevels.length; i++) {
         let indentDiff = Math.abs(indentLevels[i] - indentLevels[i - 1])
         if(indentDiff > 0){
            diffCounts[indentDiff] = (diffCounts[indentDiff] || 0) + 1
         }
      }
      let mostCommonDiff = Object.entries(diffCounts).sort((a,b) => b[1] - a[1])[0]
      return mostCommonDiff ? parseInt(mostCommonDiff[0]) : DEFAULT_INDENT
   }

   parseNvh(nvh){
      let indentSize = this.guessNvhIndentSize(nvh)
      return nvh.split('\n')
            .map(line => line.replaceAll("\t", "  "))
            .map((line, idx) => {
               if(line.trim() === ""){
                  return null
               }
               return this.parseNvhLine(line, idx, indentSize)
            })
            .filter(line => line != null)
   }

   parseNvhLine(line, idx, indentSize=2){
      if(!line.match(new RegExp(`^(([ ]{${indentSize}})*)([a-zA-Z0-9-_.]+):(.*)$`))){
         if(!line.match(new RegExp(`^([ ]{${indentSize}})*[^\\s].*`))){
            throw `Invalid indent on line ${idx + 1}: '${line.trim()}'.`
         } else if(line.match(/^[^:]*$/)){
            throw `Missing colon on line ${idx + 1}: '${line.trim()}.`
         } else if(line.match(new RegExp(`^(([ ]{${indentSize}})*)(((?!: ).)+):(.*)$`))){
            throw `Invalid element name on line ${idx + 1}: '${line.trim()}. Allowed characters: a-z, A-Z, 0-9, _, -'`
         } else{
            throw `Syntax error on line ${idx + 1}: '${line.trim()}'`
         }
      }
      let parts = line.split(/:(.*)/s) // split by first colon
      let match = parts[0].match(new RegExp(`[ ]{${indentSize}}`, "g"))
      let startsWithSpace = parts[0].startsWith(" ")
      let incorrectSpaceNum = match && parts[0].match(new RegExp(/ /g)).length % indentSize
      let indent = match ? match.length : 0
      if((idx == 0 && startsWithSpace)
         || (idx != 0 && (!startsWithSpace || incorrectSpaceNum || !match))){
         throw `Incorrect indent on line ${idx + 1}: '${line.trim()}'`
      }
      return {
         name:  parts[0].trim(),
         value: parts[1].trim(),
         indent: indent
      }
   }

   jsonToNvh(element, indent=0){
      let nvh = `${" ".repeat(indent * 2)}${element.path}: ${element.value === null ? "" : (element.value + "").replaceAll("\n", this.const.nvhNewLine)}`
         element.children && element.children.forEach(child => {
         nvh += '\n' + this.jsonToNvh(child, indent + 1)
      }, this)
      return nvh
   }

   jsonToXML(element){
      let xml = `${" ".repeat(element.indent * 2)}<${element.name}>\n`
      if(element.value){
         xml += `${" ".repeat((element.indent + 1) * 2)}${window.escapeHTML(element.value)}\n`
      }
      element.children.forEach(child => {
         xml += this.jsonToXML(child)
      }, this)
      xml += `${" ".repeat(element.indent * 2)}</${element.name}>\n`

      return xml
   }

   nvhToJson(nvh){
      let json
      let el
      let elements = this.parseNvh(nvh)
      let lastIndent = 0
      let stack = []
      elements.forEach((element, idx) => {
         if(element.indent > lastIndent + 1){
            throw `Incorrect indent on line ${idx + 1}: '${element.name}: ${element.value}'`
         }
         lastIndent = element?.indent || 0
         let parent = stack[element.indent - 1] || null
         let name = element.name.split(".").pop()
         el = {
            id: this._getNewElementId(),
            name: name,
            value: element.value.replaceAll(this.const.nvhNewLine, "\n"),
            indent: element.indent,
            parent: parent,
            children: [],
            warnings: [],
            path: parent ? `${parent.path}.${name}` : name
         }
         stack[element.indent] = el
         stack.length = element.indent + 1  // Remove keys from any deeper levels that are no longer applicable.
         if(idx == 0){
            json = el
         } else {
            el.parent?.children.push(el)
         }
      })

      return json
   }

   nvhToXML(nvh){
      let closeTags = (toIndent) => {
         while (lastIndent >= toIndent){
            xml += `${" ".repeat(lastIndent * 2)}</${openElements.shift()}>\n`
            lastIndent --
         }
      }

      let xml = ""
      let openElements = []
      let attributes = ""
      let lastIndent = 0
      let line

      nvh.split('\n').forEach((row, idx) => {
         row = row.replaceAll("\t", "  ")
         if(row.trim() != ""){
            line = this.parseNvhLine(row, idx, lastIndent)
            lastIndent && closeTags(line.indent)
            attributes = line.value ? ` xml:space="preserve"` : ""
            xml += `${" ".repeat(line.indent * 2)}<${line.name}${attributes}>\n`
            xml += `${" ".repeat((line.indent + 1) * 2)}${window.escapeHTML(line.value)}`
            openElements.unshift(line.name)
            lastIndent = line.indent
         }
      }, this)
      closeTags(0)

      return xml
   }

   XMLToJson(xml){
      let processNodeAndItsChildren = (node, parent) => {
         let element =  {
            id: this._getNewElementId(),
            name: node[0].nodeName,
            value:  node.contents().filter((i, n) => n.nodeType == Node.TEXT_NODE).text().trim(),
            indent: parent ? parent.indent + 1 : 0,
            parent: parent,
            warnings: []
         }
         element.children = node.children()
               .toArray()
               .map(childNode => processNodeAndItsChildren($(childNode), element))
         return element
      }
      let entryNode = $($.parseXML(xml)).children().first()
      let json = processNodeAndItsChildren(entryNode, null)
      return json
   }

   replaceElementNamesWithPaths(nvh){
      let lastIndent
      let lastParentPath
      let lastElementName
      let elementPath
      let nameWithIndent
      let value
      let name
      let whiteSpaces
      let match
      let indent
      return nvh.split("\n").map(row => {
         if(row.match(/^(\s*)([a-zA-Z0-9-_.]+):(.*)$/)){
            [nameWithIndent, value] = row.split(/:(.*)/s) // split by first colon
            match = nameWithIndent.match(/^\s+/)
            whiteSpaces = match ? match[0] : ""
            match = whiteSpaces.replaceAll("\t", "  ").match(new RegExp(/  /g))
            indent = match ? match.length : 0
            name = nameWithIndent.trim().split(".").pop() // just to make sure the function does not fail if there are already paths
            if(indent > lastIndent){
               lastParentPath = lastParentPath ? `${lastParentPath}.${lastElementName}` : lastElementName
            } else if(indent < lastIndent){
               lastParentPath = lastParentPath.split(".").slice(0, indent).join(".")
            }
            elementPath = lastParentPath ? `${lastParentPath}.${name}` : name
            lastIndent = indent
            lastElementName = name
            return `${whiteSpaces}${elementPath}:${value}`
         }
         return row
      }).join("\n")
   }

   replaceElementPathsWithNames(nvh){
      let pathWithIndent
      let value
      let path
      let name
      return nvh.split("\n").map(row => {
         if(row.match(/^(\s*)([a-zA-Z0-9-_.]+):(.*)$/)){
            [pathWithIndent, value] = row.split(/:(.*)/s) // split by first colon
            path = pathWithIndent.trim()
            name = path.split(".").pop()
            return `${pathWithIndent.replace(path, name)}:${value}`
         }
         return row
      }).join("\n")
   }

   areNvhJsonsEqual(element1, element2){
      return element1 && element2
            && (element1.value + "").trim() == (element2.value + "").trim()
            && element1.path == element2.path
            && element1.children.length == element2.children.length
            && element1.children.every((child1, idx) => {
               return this.areNvhJsonsEqual(child1, element2.children[idx])
            }, this)
   }

   changeEditorMode(editorMode){
      if(window.store.data.editorMode != editorMode){
         if(window.store.data.editorMode != "code"
               && this.data.customEditor
               && this.data.entry
               && window.store.data.entryId != "new"){
            this.setEntryFromCustomEditor()
            this.addStateToHistory()
            this.validateAllElements()
         }
         window.store.data.editorMode = editorMode
         this.trigger("editorModeChanged")
         this.updateUrl()
      }
   }

   setEntryFromCustomEditor(){
      if(this.data.legacyCustomEditor){
         let entry = this.XMLToJson(this.data.customEditor.harvester())
         if(this.jsonToNvh(this.data.entry) != this.jsonToNvh(entry)){
            this.data.entry = entry
         }
      } else {
         this.data.entry = this.nvhToJson(this.jsonToNvh(this.data.customEditor.getValue())) // to add all necessary properties to each element
      }
   }

   openRevisions(){
      if(!this.data.isRevisionsOpen){
         this.data.isRevisionsOpen = true
         this.trigger("isRevisionsOpenChanged")
      }
   }

   closeRevisions(){
      if(this.data.isRevisionsOpen){
         this.data.isRevisionsOpen = false
         this.trigger("isRevisionsOpenChanged")
      }
   }

   isValid(){
      return this.data.elementsMatchStructure
            && (window.store.data.editorMode != "edit"
               || !this.data.customEditor
               || this.data.legacyCustomEditor
               || this.data.customEditorIsValid)
   }

   getAvailableActions(){
      let revisions = !!this.data.revision
      let hasEntry = !!this.data.entry
      let isNewEntry = window.store.data.entryId == "new"
      let uA = window.store.data.userAccess
      return {
         new: uA.canAdd
               && !isNewEntry
               && !revisions,
         save: uA.canEdit || uA.canEditSource || (uA.canAdd && isNewEntry)
               && hasEntry
               && !this.data.isSaving
               // valid?
               && (
                     (window.store.data.editorMode == "edit"
                           && this.data.customEditor
                           && (this.data.legacyCustomEditor ? this.data.elementsMatchStructure : this.data.customEditorIsValid)
                     )
                     || (((window.store.data.editorMode == "view" )
                           || window.store.data.editorMode == "edit" && !this.data.customEditor
                           || window.store.data.editorMode == "code")
                           && this.isValid()
                        )
                  )
               && !revisions,
         toggleCompleted: window.store.data.config.progress_tracking?.tracked
               && hasEntry
               && !isNewEntry
               && (uA.canEdit || uA.canEditSource)
               && !revisions,
         undo: (uA.canEdit || uA.canEditSource)
               && this.history.actualIdx > 0
               && !revisions,
         redo: (uA.canEdit || uA.canEditSource)
               && (this.history.actualIdx < this.history.states.length - 1)
               && !revisions,
         duplicate: uA.canAdd
               && uA.canEdit
               && hasEntry
               && !isNewEntry
               && !revisions,
         delete: uA.canDelete
               && !isNewEntry
               && !revisions,
         view: uA.canView
               && hasEntry
               && !isNewEntry,
         edit: (uA.canEdit || (uA.canAdd && isNewEntry))
               && hasEntry,
         code: uA.canEditSource
               && (hasEntry || !!this.data.brokenEntryNvh),
         history: (uA.canEdit || uA.canEditSource)
               && !isNewEntry
      }
   }

   getElementList(element, list=[]){
      element = element || this.data.entry
      if(element){
         list.push(element)
         element.children.forEach(child => {
            this.getElementList(child, list)
         }, this)
      }
      return list
   }

   getPrevElement(element, onlyVisible){
      let elementList = this.getElementList()
      let idx = elementList.indexOf(element) - 1
      let el = elementList[idx]
      if(el && onlyVisible){
         while(el && !this.isElementVisible(el)){
            el = elementList[idx--]
         }
      }
      return el
   }

   getNextElement(element, onlyVisible){
      let elementList = this.getElementList()
      let idx = elementList.indexOf(element) + 1
      let el = elementList[idx]
      if(el && onlyVisible){
         while(el && !this.isElementVisible(el)){
            el = elementList[idx++]
         }
      }
      return el
   }

   getFocusedElement(){
      return this.findElement(e => e.focused)
   }

   getElementConfig(elementPath){
      if(this.isServiceElement(elementPath)){
         return {
            type: "string",
            children: []
         }
      }
      return this.schema.getElementByPath(elementPath)
   }

   getElementStyle(elementPath){
      return this.data.formatting.elements[elementPath]
   }

   getAvailableChildElementPaths(element){
      let config = this.getElementConfig(element.path)
      if(config){
         return config.children.filter(childConfig => {
            return this.canHaveAnotherChild(element, childConfig.path)
         }).map(childConfig => childConfig.path)
      }
      return []
   }

   canHaveAnotherChild(element, childPath){
      if(this.isServiceElement(childPath)){
         return true
      } else {
         let childConfig = this.getElementConfig(childPath)
         return !childConfig.max || childConfig.max > element.children.filter(c => c.path == childPath).length
      }
   }

   getAvailableParentElements(elementPath){
      let parentPath = this.getElementConfig(elementPath)?.parent?.path || ""
      return this.findElements(parent => parent.path == parentPath)
   }

   getNextAvailableParentInDirection(element, direction){
      let availableParents = this.getAvailableParentElements(element.path)
      let idx = availableParents.indexOf(element.parent) + direction
      while (availableParents[idx] && !this.canHaveAnotherChild(availableParents[idx], element.path)){
         idx += direction
      }
      return availableParents[idx]
   }

   getElementAncestors(element){
      let ancestors = []
      let parent = element.parent
      while (parent){
         ancestors.push(parent)
         parent = parent.parent
      }
      return ancestors
   }

   getElementHTMLTag(element){
      return $(`#nvh-item-${element.id}`)
   }

   changeElementStyleOption(elementPath, option, value){
      if(this.getElementStyle(elementPath)[option] != value){
         // TODO temporary fix
         if(!this.data.formatting.elements[elementPath]){
            this.data.formatting.elements[elementPath] = {}
         }
         if(!value){
            delete this.data.formatting.elements[elementPath][option]
         } else {
            this.data.formatting.elements[elementPath][option] = value
         }
         let elements = this.findElements(e => e.path == elementPath)
         let config = this.getElementConfig(elementPath)
         if(config && config.type == "markup"){
            // markup element style changed - parent element must be updated
            config.parent && elements.push(config.parent.path)
         }

         this.trigger("updateElements", elements)
      }
   }

   isEntryCompleted(){
      if(window.store.data.config.progress_tracking?.tracked){
         let completedValue = this.findElement(el => el.name == "__lexonomy__complete")?.value
         return completedValue && !["false", "0", "no"].includes(completedValue)
      }
      return false
   }

   isElementVisible(element){
      let el = element
      while (el.parent && !el.parent.collapsed){
         el = el.parent
      }
      return !el.parent || !el.parent.collapsed
   }

   isElementViewable(element){
      let specialElements = ["relation"]
      return this.data.structure.mode != "dmlex"
            || (!specialElements.includes(element.name)
                  && !this.getElementAncestors(element)
                     .some(el => {return specialElements.includes(el.name)})
               )
   }

   isElementDescendantOf(element, possibleParent){
      let el = element
      while(el.parent){
         if(el.parent == possibleParent){
            return true
         }
         el = el.parent
      }
      return false
   }

   isServiceElement(elementPath){
      return elementPath.split(".").pop().startsWith(this.const.serviceElementPrefix)
   }

   copyElementAndItsChildren(element, parent=null){
      let copy = {
         id: Math.round(Math.random() * 1000000),
         parent: parent,
         children: [],
         warnings: []
      }
      Object.entries(element).forEach(([key, data]) => {
         if(key == "children"){
            data.forEach(c => {
               copy.children.push(this.copyElementAndItsChildren(c, copy))
            })
         } else if(key == "parent"){

         } else if(["edit", "focused"].includes(key)) {
            copy[key] = false
         } else {
            copy[key] = data
         }
      })
      return copy
   }

   forEachElement(callback, element){
      element = element || this.data.entry
      callback(element)
      element.children.forEach(this.forEachElement.bind(this, callback))
   }

   findElement(callback, rootElement){
      return this.getElementList(rootElement).find(callback)
   }

   findElements(callback, rootElement){
      return this.getElementList(rootElement).filter(callback)
   }

   getElementById(id){
      return this.findElement(e => e.id == id)
   }

   focusElement(element){
      if(element && !element.focused){
         let elements = this.findElements(e => e.focused || e.edit)
         this.forEachElement(e => {
            e.focused = e == element
            e.edit = false
         })
         this.trigger("updateElements", [...elements, element])
      }
   }

   blurElement(){
      let elements = this.findElements(e => e.focused || e.edit)
      elements.forEach(e => {
         e.focused = false
         e.edit = false
      })
      this.trigger("updateElements", elements)
   }

   focusFirstElement(){
      if(window.store.data.editorMode == "edit"){
         this.focusElement(this.data.entry)
         $(".nvh-focused").focus()
      }
   }

   toggleElementCollapsed(element){
      if(element.collapsed){
         this.expandElement(element)
         this.data.collapsedElements.delete(element.path)
      } else {
         this.collapseElement(element)
         this.data.collapsedElements.add(element.path)
      }
   }

   expandElement(element){
      element = element || this.getFocusedElement()
      if(element.children.length && element.collapsed){
         element.collapsed = false
         this.data.collapsedElements.delete(element.path)
         this.trigger("elementCollapsedChanged", element)
      }
   }

   collapseElement(element){
      element = element || this.getFocusedElement()
      if(element.children.length && !element.collapsed){
         element.collapsed = true
         this.data.collapsedElements.add(element.path)
         let focused = this.getFocusedElement()
         if(element.collapsed && focused && this.isElementDescendantOf(focused, element)){
            this.focusElement(element)
         }
         this.trigger("elementCollapsedChanged", element)
      }
   }

   makeElementVisible(element){
      if(!this.isElementVisible(element)){
         this.getElementAncestors(element).forEach(this.expandElement, this)
      }
   }

   goToPrevElement(){
      this.focusElement(this.getPrevElement(this.getFocusedElement(), true))
      this.scrollElementIntoView(this.getFocusedElement())
   }

   goToNextElement(){
      this.focusElement(this.getNextElement(this.getFocusedElement(), true))
      this.scrollElementIntoView(this.getFocusedElement())
   }

   openElementToolbar(element){
      this.focusElement(element)
      this.trigger("openItemToolbar", element)
   }

   closeElementToolbar(element){
      this.blurElement(element)
      this.trigger("closeItemToolbar", element)
   }

   startElementEditing(element){
      let config = this.getElementConfig(element.path)
      if(config && !["empty", "markup"].includes(config.type)){
         let elements = this.findElements(e => e.focused || e.edit)
         elements.forEach(e => {
            e.focused = e == element,
            e.edit = false
         })
         element.focused = true
         element.edit = true
         this.trigger("closeContextMenu")
         this.trigger("closeItemToolbar")
         this.trigger("updateElements", [...elements, element])
      }
   }

   startElementOrChildEditing(element){
      let firstEditableElement = this.findElement(el => {
         let config = this.getElementConfig(el.path)
         // TODO exclude markup elemnets and its children
         return config && config.type != "empty"
      }, element)
      firstEditableElement && this.startElementEditing(firstEditableElement)
   }

   stopElementEditing(){
      let elements = this.findElements(element => element.edit)
      elements.forEach(element => {
         if(element.isNew){
            // element was created and its value was not changed before calling this method -> remove new element
            let childIdx = element.parent.children.findIndex(e => e == element)
            element.parent.children.splice(childIdx, 1)
            this.trigger("updateElements", [element.parent])
         } else {
            element.edit = false
         }
      })
      this.trigger("updateElements", elements)
   }

   changeElementValue(element, value){
      delete element.isNew
      if(element.value != value){
         element.value = value
         this.addStateToHistory()
      }
      this.trigger("updateElements", [element])
   }

   startElementDragging(element){
      this.data.draggedElement = element
      element.focused = false
      this.trigger("onDndStart")
   }

   stopElementDragging(){
      this.data.draggedElement = null
      this.trigger("onDndStop")
   }

   moveChildToAnotherParent(element, newParent, position=0){
      let oldParentReference = element.parent
      let idx = element.parent.children.indexOf(element)
      element.parent.children.splice(idx, 1)
      element.parent = newParent
      if(position === null){
         newParent.children.push(element)
      } else {
         newParent.children.splice(position, 0, element)
      }
      this.trigger("updateElements", [oldParentReference, newParent])
      this.addStateToHistory()
   }

   moveElementUp(element){
      if(element.parent.children.indexOf(element) > 0){
         this.moveElementWithinSiblings(element, -1)
      } else {
         this.moveElementToPreviousParent(element)
      }
   }

   moveElementDown(element){
      if(element.parent.children.indexOf(element) < element.parent.children.length - 1){
         this.moveElementWithinSiblings(element, 1)
      } else {
         this.moveElementToNextParent(element)
      }
   }

   moveElementToPreviousParent(element){
      this.moveElementToParentInDirection(element, -1)
   }

   moveElementToNextParent(element){
      this.moveElementToParentInDirection(element, 1)
   }

   moveElementWithinSiblings(element, direction){
      let childIdx = element.parent.children.indexOf(element)
      let newChildIdx = childIdx + direction
      if(newChildIdx >= 0 && newChildIdx < element.parent.children.length){
         element.parent.children.splice(childIdx, 1)
         element.parent.children.splice(childIdx + direction, 0, element)
         this.trigger("updateElements", [element.parent])
         this.addStateToHistory()
         this.scrollElementIntoViewDebounced()
      }
   }

   moveElementToParentInDirection(element, direction){
      let newParent = this.getNextAvailableParentInDirection(element, direction)
      if(newParent){
         this.moveChildToAnotherParent(element, newParent, direction == 1 ? 0 : null)
         this.scrollElementIntoViewDebounced()
      }
   }

   addChildElement(element, childElementPath, position){
      let childElement = this._addChildElement(element, childElementPath, position)
      this.addNewFlagToElement(childElement)
      this.addRequiredChildren(childElement)
      this.trigger("updateElements", [element])
      this.trigger("closeContextMenu")
      this.startElementOrChildEditing(childElement)
      this.addStateToHistory()
   }

   addSiblingElement(element, siblingElementPath, position){
      let idx = element.parent.children.indexOf(element) + (position == 'after' ? 1 : 0)
      let siblingElement = this._addChildElement(element.parent, siblingElementPath, idx)
      this.addNewFlagToElement(siblingElement)
      this.addRequiredChildren(siblingElement)
      this.trigger("updateElements", [element.parent])
      this.trigger("closeContextMenu")
      this.startElementOrChildEditing(siblingElement)
      this.addStateToHistory()
   }

   addRequiredChildren(element){
      this.getElementConfig(element.path)?.children.forEach(childConfig => {
         if(childConfig.min > 0){
            Array.from({length: childConfig.min}).forEach(empty => {
               let childElement = this._addChildElement(element, childConfig.path)
               this.addRequiredChildren(childElement)
            })
         }
      })
   }

   addAllChildren(element){
      let structure = this.data.structure
      let config = this.getElementConfig(element.path)
      config && config.children.forEach(childConfig => {
         if(structure.hasNewEntryTemplate){
            // add child elements acording to settings in new entry emplate
            if(structure.newEntryTemplate.defaultElements[childConfig.path]){
               let childElement = this._addChildElement(element, childConfig.path)
               this.addAllChildren(childElement)
            }
         } else {
            // add child elements to meet minimum child elements of given type
            Array.from({length: childConfig.min}).forEach(empty => {
               let childElement = this._addChildElement(element, childConfig.path)
               this.addAllChildren(childElement)
            })
         }
      })
   }

   addNewFlagToElement(element){
      let config = this.getElementConfig(element.path)
      if(config && !["list", "bool"].includes(config.type)){
         // "list" or "bool" elements are created instantly, other elements are removed
         // in stopElementEditing(), unless they were saved before. So user can undo
         // element-creating action with ESC in value editor
         element.isNew = true
      }
   }

   _addChildElement(element, childElementPath, idx){
      let childElement = {
         id: this._getNewElementId(),
         path: childElementPath,
         name: childElementPath.split(".").pop(),
         value: this._getElementDefaultValue(childElementPath),
         indent: element.indent + 1,
         parent: element,
         children: [],
         warnings: []
      }
      if(typeof idx == "undefined"){
         element.children.push(childElement)
      } else {
         element.children.splice(idx, 0, childElement)
      }
      return childElement
   }

   removeElement(element){
      let globalIdx = this.getElementList().indexOf(element)
      let childIdx = element.parent.children.findIndex(e => e == element)
      element.parent.children.splice(childIdx, 1)
      let elementList = this.getElementList()
      let siblingElement = elementList[globalIdx] || elementList[globalIdx - 1] // next or previous element
      if(siblingElement){
         this.forEachElement(e => {e.focused = e == siblingElement})
         this.trigger("updateElements", [element.parent, siblingElement])
      } else {
         this.trigger("updateElements", [element.parent])
      }
      this.trigger("closeContextMenu")
      this.addStateToHistory()
   }

   duplicateElement(element){
      let elementCopy = this.copyElementAndItsChildren(element, element.parent)
      let idx = element.parent.children.indexOf(element)
      element.parent.children.splice(idx + 1, 0, elementCopy)
      this.addNewFlagToElement(elementCopy)
      this.trigger("updateElements", [element.parent])
      this.trigger("closeContextMenu")
      this.startElementOrChildEditing(elementCopy)
      this.addStateToHistory()
   }

   removeAllChildren(element){
      element.children = []
      this.trigger("updateElements", [element])
      this.addStateToHistory()
   }

   scrollElementIntoViewDebounced(){
      this.scrollDebounceTimer && clearTimeout(this.scrollDebounceTimer)
      this.scrollDebounceTimer = setTimeout(() => {
         clearTimeout(this.scrollDebounceTimer)
         let focusedElement = this.getFocusedElement()
         focusedElement && this.scrollElementIntoView(focusedElement, true)
      }, 100)
   }

   scrollElementIntoView(element, animate){
      let node = this.getElementHTMLTag(element).find(">.nvh-item>.nvh-wrapper")
      if(node.length){  // page might change
         let elementHeight = node.outerHeight()
         let elementTop = node.offset().top
         let elementBottom = elementTop + elementHeight
         let viewportTop = $(window).scrollTop()
         let windowHeight = $(window).height()
         let viewportBottom = viewportTop + windowHeight
         let scrollTop = null
         if(elementTop < viewportTop + 100){
            scrollTop = elementTop - 100
         } else if(elementBottom > viewportBottom - 100 && elementHeight < (windowHeight - 100)){
            scrollTop = elementBottom - windowHeight + 100
         }
         if(scrollTop !== null){
            if(animate){
               $("html, body").animate({scrollTop: scrollTop}, 200)
            } else {
               document.documentElement.scrollTop = scrollTop
            }
         }
      }
   }

   isElementEditAllowed(element){
      let type = this.getElementConfig(element.path)?.type
      return !["empty", "markup"].includes(type)
   }

   isElementDuplicationAllowed(element){
      return element.name != this.data.rootElement
            && !!element.parent
            && this.getElementConfig(element.path)?.type != "markup"
            && this.canHaveAnotherChild(element.parent, element.path)
   }

   isElementRemovalAllowed(element){
      if(element.name == this.data.rootElement){
         return false
      }
      let config = this.getElementConfig(element.path)
      if(config){
         let actualNumberOfElements = this.findElements(e => e.path == element.path, element.parent).length
         return element.name != this.data.rootElement
               && (!config.min || config.min < actualNumberOfElements)
      }
      return true
   }

   validateElement(element){
      if(element == this.data.detachedEntry || this.isServiceElement(element.path)){
         element.warnings = []
         element.isValid = true
      } else {
         let config = this.getElementConfig(element.path)
         let warnings = []
         if(!config || !config.type){  // has valid configuration
            warnings.push(`Unknown element "${element.name}".`)
         } else {
            if(config.type == "empty"){
               if(element.value){
                  warnings.push(`Element "${element.name}" should not have any text.`)
               }
            } else if(config.type == "string"){
               if(config.re){
                  let re = new RegExp(config.re)
                  if(!re.test(element.value)){
                     warnings.push(`Element "${element.name}" does not match regular expression.`)
                  }
               }
            } else if(config.type == "list"){
               if(!element.value){
                  warnings.push(`Element "${element.name}" should not be empty.`)
               } else if(!config.values.includes(element.value)){
                  warnings.push(`Element "${element.name}" should not have the value "${element.value}".`)
               }
            }
            // TODO zruseno kvuli flagum, chceme zrejme umoznit definovat required u elementu
            /*if(config.type != "empty"){
               if(!element.value){
                  warnings.push(`Element "${element.name}" should have some text.`)
               }
            }*/
            let counts = element.children.reduce((counts, e) => {
               counts[e.path] = counts[e.path] ? counts[e.path] + 1 : 1
               return counts
            }, {})
            config.children.forEach(childConfig => {
               if(childConfig){
                  let childPath = childConfig.path
                  if (childConfig.max && (counts[childConfig] || 0) > childConfig.max){
                     warnings.push(`Element "${element.name}" should have at most ${childConfig.max} "${childPath}"`)
                  }
                  if (childConfig.min && (counts[childPath] || 0) < childConfig.min){
                     warnings.push(`Element "${element.name}" should have at least ${childConfig.min} "${childPath}"`)
                  }
               }
            })
            element.children.forEach(child => {
               if(!this.isServiceElement(child.path)){
                  if(!this.schema.getElementByPath(child.path)){
                     warnings.push(`'${element.path}' has unknown child element '${child.path}'.`)
                  } else if(!config.children.find(childConfig => childConfig.path == child.path)){
                     warnings.push(`'${element.path}' must not have '${child.path}' as child element.`)
                  }
               }
            })
         }

         element.warnings = [...new Set(warnings)] // remove duplicities
         element.isValid = !warnings.length
      }
      let isValid = !this.findElement(e => !e.isValid)
      if(this.data.elementsMatchStructure != isValid){
         this.data.elementsMatchStructure = isValid
         this.trigger("isValidChanged")
      }
   }

   validateElements(elements){
      elements.forEach(this.validateElement.bind(this))
   }

   validateAllElements(){
      this.forEachElement(this.validateElement.bind(this))
   }

   _getNewElementId(){
       // needed for riot to track changes properly
      return this.data.lastElementId++
   }

   _getElementDefaultValue(elementPath){
      if(this.data.structure.hasNewEntryTemplate){
         return this.data.structure.newEntryTemplate?.defaultValues[elementPath] || ""
      } else {
         let config = this.getElementConfig(elementPath)
         if(config){
            if(config.type == "empty"){
               return null
            } else if(config.type == "bool"){
               return 0
            } else if(config.type == "list" && config.values.length){
               return config.values[0]
            }
         }
      }
      return ""
   }

   _getNewEntry(){
      let entry
      entry = {
         id: this._getNewElementId(),
         path: this.data.rootElement,
         name: this.data.rootElement,
         parent: null,
         indent: 0,
         value: this._getElementDefaultValue(this.data.rootElement),
         children: []
      }
      this.addAllChildren(entry)
      return entry
   }

   addStateToHistory(){
      let nvh = this.jsonToNvh(this.data.entry)
      this.history.addState(this.replaceElementPathsWithNames(nvh))
   }

   onHistoryStateChange(idx, nvh){
      this.updateEntryNvh(nvh)
   }

   updateUrl(){
      let dictData = window.store.data
      let newUrl = `${window.location.href.split("#")[0]}#/${dictData.dictId}/edit/`
      if(dictData.entryId != null){
         newUrl += `${dictData.entryId}/${window.store.data.editorMode}${window.store.getEntrySearchUrlQueryString()}`
      }
      if(newUrl != window.location.href){
         history.pushState(null, null, newUrl)
         route.base() // need to update route's "current" value in
                       //order to browser back button works correctly
      }
   }

   replaceMarkupOccurrences(value, element, createReplaceString) {
      let replaceList = []
      element.children.filter(child => this.getElementConfig(child.path)?.type == "markup")
            .forEach(child => {
               let hashIndex = child.value.lastIndexOf("#")
               let find = child.value
               let occurrenceIndex = 1
               if(hashIndex != -1 && child.value.charAt(hashIndex - 1) != "#"){
                  find = child.value.substr(0, hashIndex)
                  occurrenceIndex = child.value.substr(hashIndex + 1)
               }
               find = find.replaceAll("##", "#")
               if(find.trim()){
                  let index = window.getNthSubstringIndex(value, find, occurrenceIndex || 1)
                  if(index !== -1){
                     let replaceWith = createReplaceString(child.path, find, child)
                     replaceList.push({
                        index: index,
                        find: find,
                        replaceWith: replaceWith
                     })
                  }
               }
            })
      // Replace occurrences from the end of the so the indexes will be still valid after each replacing.
      replaceList.sort((a, b) => b.index - a.index)
            .forEach(replaceObj => {
               value = value.slice(0, replaceObj.index)
                     + replaceObj.replaceWith
                     + value.slice(replaceObj.index + replaceObj.find.length)
            })
      return value
   }

   getElementTreeList(elementPath, indent=0){
      let element = this.schema.getElementByPath(elementPath || this.schema.getRoot()?.path)
      return this.schema.jsonToList(element).map(element => ({
         path: element.path,
         indent: element.indent,
         color: this.getElementColor(element.path)
      }))
   }

   getElementColor(elementPath){
      return this.schema.getPathColor(elementPath)
   }
}

window.nvhStore = new NVHStoreClass()
