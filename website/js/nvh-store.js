class NVHStoreClass {
   constructor(){
      this.lastId = 0
      this.const = {
         nvhNewLine: "\\\\n",
         serviceElementPrefix: "__lexonomy__"
      }
      this.data = {
         entry: null,
         // used to store droped items into side panel
         detachedEntry: {
            children: []
         },
         isDMLexCompatible: true, // TODO add new setting to dictionary
         isContextMenuOpen: false,
         isRevisionsOpen: false,
         draggedElement: null,
         rootElement: null
      }
      observable(this)
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
      this.history.addState()
      window.store.data.editorMode == "view" && this.changeEditorMode("edit")
      this.trigger("entryChanged")
      this.updateUrl()
      this.focusFirstElement()
   }

   saveEntry(){
      this.data.isSaving = true
      this.trigger("isSavingChanged")
      if(this.data.customEditor && window.store.data.editorMode != "code"){
         this.setEntryFromCustomEditor()
      }
      let nvh = this.jsonToNvh(this.data.entry)
      if(window.store.data.entryId != "new"){
         return window.store.updateEntry(nvh)
               .always(response => {
                  if(response.success){
                     M.toast({html: "Entry updated"})
                     this.history.lastSavedIdx = this.history.actualIdx
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
                  this.history.lastSavedIdx = this.history.actualIdx
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
               this.history.addState()
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
                     this.trigger("entryChanged")
                     this.updateUrl()
                  } else {
                     M.toast({html: `Entry was not deleted: ${response.feedback}`})
                  }
                  this.data.isSaving = false
                  this.trigger("isSavingChanged")
               })
      } else{
         this.data.entry = null
         this.trigger("entryChanged")
         this.updateUrl()
      }
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
      this.data.rootElement = this.data.structure.root
      this.data.customEditor = null
      this.data.legacyCustomEditor = false
      if(this.data.editing.useOwnEditor){
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
      if(window.store.data.entryId){
         if(window.store.data.entryId == "new"){
            this.data.entry = this._getNewEntry()
         } else{
            this.data.entry = this.nvhToJson(this.replaceElementNamesWithPaths(window.store.data.entry.nvh))
         }
         this.validateAllElements()
         this.history.addState()
      } else {
         this.data.entry = null
      }
      this.trigger("entryChanged")
   }

   editorNeedsSaving(evt) {
      if(window.store.data.actualPage == "dict-edit"
            && (this.data.entryId == "new"
                  || (window.store.data.entry
                           && this.data.entry
                           && this.hasEntryChanged()
                     )
               )
            ){
         if(!confirm("You have some unsaved changes. Do you wish to continue and discard the changes?")){
            if(evt){
               evt.stopImmediatePropagation()
               evt.stopPropagation()
               evt.preventDefault()
            }
            return true
         }
      }
      return false
   }

   hasEntryChanged(){
      return !this.areNvhJsonsEqual(this.data.entry, this.nvhToJson(window.store.data.entry.nvh))
   }

   showRevision(revision){
      if(revision){
         try{
            this.data.storedEntry = this.data.entry
            this.data.entry = this.nvhToJson(revision.content)
            this.data.revision = revision
            this.validateAllElements()
         } catch(e){
            // TODO it should be possible to open nvh source code and let user to fix the issue
            M.toast({html: "Revision data corrputed."})
         }
      } else{
         this.data.revision = null
         this.data.entry = this.data.storedEntry
         this.data.storedEntry = null
      }
      this.trigger("updateEditor")
   }

   restoreRevision(){
      this.data.revision = null
      this.data.storedEntry = null
      //this.history.addState()
      this.closeRevisions()
      this.saveEntry()
      this.trigger("updateEditor")
   }

   parseNvhLine(line, idx, lastIndent){
      if(!line.match(/^(([ ]{2})*)([a-zA-Z0-9-_.]+):(.*)$/)){
         if(line.match(/^( {2})* [^ ]/)){
            throw `Invalid indent on line ${idx + 1}: '${line.trim()}'.`
         } else if(line.match(/^[^:]*$/)){
            throw `Missing colon on line ${idx + 1}: '${line.trim()}.`
         } else if(line.match(/^(([ ]{2})*)(((?!: ).)+):(.*)$/)){
            throw `Invalid element name on line ${idx + 1}: '${line.trim()}. Allowed characters: a-z, A-Z, 0-9, _, -'`
         } else{
            throw `Syntax error on line ${idx + 1}: '${line.trim()}'`
         }
      }
      let parts = line.split(/:(.*)/s) // split by first colon
      let match = parts[0].match(new RegExp(/  /g))
      let startsWithSpace = parts[0].startsWith(" ")
      let evenSpaceNum = match && parts[0].match(new RegExp(/ /g)).length % 2
      let indent = match ? match.length : 0
      if((idx == 0 && startsWithSpace)
         || (idx != 0 && (!startsWithSpace || evenSpaceNum || !match))
         || (indent > lastIndent + 1)){
         throw `Incorrect indent on line ${idx + 1}: '${line.trim()}'`
      }
      return {
         name:  parts[0].trim(),
         value: parts[1].trim(),
         indent: indent
      }
   }

   jsonToNvh(element, indent=0, fullPath=true){
      let key = fullPath ? element.name : element.name.split(".").pop()
      let nvh = `${" ".repeat(indent * 2)}${key}: ${element.value === null ? "" : (element.value + "").replaceAll("\n", this.const.nvhNewLine)}\n`
         element.children && element.children.forEach(child => {
         nvh += this.jsonToNvh(child, indent + 1, fullPath)
      }, this)
      return nvh
   }

   jsonToXML(element){
      let xml = `${" ".repeat(element.indent * 2)}<${element.name}>\n`
      if(element.value){
         xml += `${" ".repeat((element.indent + 1) * 2)}${this.escapeXMLValue(element.value)}\n`
      }
      element.children.forEach(child => {
         xml += this.jsonToXML(child)
      }, this)
      xml += `${" ".repeat(element.indent * 2)}</${element.name}>\n`

      return xml
   }

   nvhToJson(nvh){
      const getParent = indent => {
         if(!indent){
            return null
         } else if (indent == 1){
            return json
         } else {
            let actualLevel = 1
            let parent = json
            while (actualLevel < indent){
               parent = parent.children[parent.children.length - 1]
               actualLevel++
            }
            return parent
         }
      }
      let json
      let line
      let el
      nvh.split('\n').forEach((row, idx) => {
         row = row.replaceAll("\t", "  ")
         if(row.trim() != ""){
            line = this.parseNvhLine(row, idx, el ? el.indent : 0)
            let parent = getParent(line.indent)
            el = {
               id: this._getNewElementId(),
               name: line.name,
               value: line.value.replaceAll(this.const.nvhNewLine, "\n"),
               indent: line.indent,
               parent: parent,
               children: [],
               warnings: [],
               path: parent ? `${parent.path}.${line.name}` : line.name
            }
            if(idx == 0){
               json = el
            } else {
               el.parent.children.push(el)
            }
         }
      }, this)

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
            xml += `${" ".repeat((line.indent + 1) * 2)}${this.escapeXMLValue(line.value)}`
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

   nvhSchemaToJSON(nvhSchema){
      let json = this.nvhToJson(nvhSchema)
      this.getElementList(json).forEach(el => {
         Object.assign(el, this.parseNvhSchemaOptionsValue(el.value))
      })
      return json
   }

   nvhSchemaToNewEntryTemplate(nvhSchema){
      let nvh = ""
      let addElementAndChildren = (element) => {
         nvh += `${" ".repeat(element.indent * 2)}${element.name}:\n`
         element.children.forEach(child => {
            if(child.min){
               for(let i = 0; i < child.min; i++){
                  addElementAndChildren(child)
               }
            }
         })
      }
      addElementAndChildren(this.nvhSchemaToJSON(nvhSchema))
      return nvh
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

   areNvhJsonsEqual(element1, element2){
      return element1 && element2
            && (element1.value + "").trim() == (element2.value + "").trim()
            && element1.children.length == element2.children.length
            && element1.children.every((child1, idx) => {
               return this.areNvhJsonsEqual(child1, element2.children[idx])
            }, this)
   }

   changeEditorMode(editorMode){
      if(window.store.data.editorMode != editorMode){
         if(window.store.data.editorMode != "code" && this.data.customEditor && window.store.data.entryId != "new"){
            this.setEntryFromCustomEditor()
            this.history.addState()
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
            && (!this.data.customEditor || this.data.legacyCustomEditor || this.data.customEditorIsValid)
   }

   getAvailableActions(){
      let revisions = !!this.data.revision
      let hasEntry = !!this.data.entry
      let isNewEntry = window.store.data.entryId == "new"
      let uA = window.store.data.userAccess
      return {
         new: uA.canEdit
               && !isNewEntry
               && !revisions,
         save: uA.canEdit
               && hasEntry
               && !this.data.isSaving
               // valid?
               && (this.data.customEditor || this.isValid())
               && (!this.data.customEditor || (this.data.legacyCustomEditor ? this.data.elementsMatchStructure : this.data.customEditorIsValid))
               // anything to save ?
               && (this.history.actualIdx != this.history.lastSavedIdx
                        || window.store.data.entryId == "new"
                        || window.store.data.editorMode == "code"
                        || this.data.customEditor
                  )
               && !revisions,
         undo: uA.canEdit
               && this.history.actualIdx > 0
               && !revisions,
         redo: uA.canEdit
               && (this.history.actualIdx < this.history.records.length - 1)
               && !revisions,
         add: uA.canEdit,
         duplicate: uA.canEdit
               && hasEntry
               && !isNewEntry
               && !revisions,
         delete: uA.canEdit
               && hasEntry
               && !isNewEntry
               && !revisions,
         view: hasEntry
               && !isNewEntry,
         edit: uA.canEdit
               && hasEntry,
         code: uA.canEdit
               && hasEntry,
         history: uA.canEdit
               && hasEntry
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

   getElementConfig(elementName){
      if(this.isServiceElement(elementName)){
         return {
            type: "string",
            children: []
         }
      }
      return this.data.structure.elements[elementName]
   }

   getElementStyle(elementName){
      return this.data.formatting.elements[elementName]
   }

   getAvailableChildElements(element){
      let config = this.data.structure.elements[element.name]
      let elements = []
      if(config){
         elements = config.children.filter(childName => {
            return this.canHaveAnotherChild(element, childName)
         })
      }
      return elements
   }

   canHaveAnotherChild(element, childName){
      if(this.isServiceElement(childName)){
         return true
      } else {
         let childConfig = this.data.structure.elements[childName]
         return !childConfig.max || childConfig.max > element.children.filter(c => c.name == childName).length
      }
   }

   getAvailableParentElementNames(elementName){
      let elements = this.data.structure.elements
      if(this.isServiceElement(elementName)){
         return Object.keys(elements)
      } else {
         return Object.keys(elements).filter(parentName => {
            return elements[parentName].children.some(child => child == elementName)
         })
      }
   }

   getAvailableParentElements(elementName){
      let availableParentNames = this.getAvailableParentElementNames(elementName)
      return this.findElements(parent => {
         return availableParentNames.includes(parent.name)
      })
   }

   getNextAvailableParentInDirection(element, direction){
      let availableParents = this.getAvailableParentElements(element.name)
      let idx = availableParents.indexOf(element.parent) + direction
      while (availableParents[idx] && !this.canHaveAnotherChild(availableParents[idx], element.name)){
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

   changeElementStyleOption(elementName, option, value){
      if(this.getElementStyle(elementName)[option] != value){
         // TODO temporary fix
         if(!this.data.formatting.elements[elementName]){
            this.data.formatting.elements[elementName] = {}
         }
         if(!value){
            delete this.data.formatting.elements[elementName][option]
         } else {
            this.data.formatting.elements[elementName][option] = value
         }
         let elements = this.findElements(e => e.name == elementName)
         let config = this.getElementConfig(elementName)
         if(config && config.type == "markup"){
            elements = elements.map(e => {
               // markup element style changed - parent element must be updated
               return [e, ...this.getAvailableParentElements(e.name)]
            }).flat()
         }

         this.trigger("updateElements", elements)
      }
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
      return !this.data.isDMLexCompatible
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

   isServiceElement(elementName){
      return elementName.startsWith(this.const.serviceElementPrefix)
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
      element.collapsed ? this.expandElement(element) : this.collapseElement(element)
   }

   expandElement(element){
      element = element || this.getFocusedElement()
      if(element.children.length && element.collapsed){
         element.collapsed = false
         this.trigger("elementCollapsedChanged", element)
      }
   }

   collapseElement(element){
      element = element || this.getFocusedElement()
      if(element.children.length && !element.collapsed){
         element.collapsed = true
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
      let config = this.getElementConfig(element.name)
      if(config && config.type != "empty"){  // element with value
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
         let config = this.getElementConfig(el.name)
         return config && config.type != "empty"
      }, element)
      firstEditableElement && this.startElementEditing(firstEditableElement)
   }

   stopElementEditing(){
      let elements = this.findElements(e => e.edit)
      elements.forEach(e => {e.edit = false})
      this.trigger("updateElements", elements)
   }

   changeElementValue(element, value){
      if(element.value != value){
         element.value = value
         this.history.addState()
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
      this.history.addState()
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
         this.history.addState()
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

   addChildElement(element, childElementName){
      let childElement = this._addChildElement(element, childElementName)
      this.addRequiredChildren(childElement)
      this.trigger("updateElements", [element])
      this.trigger("closeContextMenu")
      this.startElementOrChildEditing(childElement)
      this.history.addState()
   }

   addSiblingElement(element, siblingElementName, position){
      let idx = element.parent.children.indexOf(element) + (position == 'after' ? 1 : 0)
      let siblingElement = this._addChildElement(element.parent, siblingElementName, idx)
      this.addRequiredChildren(siblingElement)
      this.trigger("updateElements", [element.parent])
      this.trigger("closeContextMenu")
      this.startElementOrChildEditing(siblingElement)
      this.history.addState()
   }

   addRequiredChildren(element){
      let config = this.getElementConfig(element.name)
      config && config.children.forEach(childName => {
         let childConfig = this.getElementConfig(childName)
         if(childConfig.min > 0){
            Array.from({length: childConfig.min}).forEach(empty => {
               let childElement = this._addChildElement(element, childName)
               this.addRequiredChildren(childElement)
            })
         }
      })
   }

   addAllChildren(element){
      let config = this.getElementConfig(element.name)
      config && config.children.forEach(childName => {
         let childConfig = this.getElementConfig(childName)
         Array.from({length: childConfig.min || 1}).forEach(empty => {
            let childElement = this._addChildElement(element, childName)
            this.addAllChildren(childElement)
         })
      })
   }

   _addChildElement(element, childElementName, idx){
      let childElement = {
         id: this._getNewElementId(),
         name: childElementName,
         value: this._getElementDefaultValue(childElementName),
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
      this.history.addState()
   }

   duplicateElement(element){
      let elementCopy = this.copyElementAndItsChildren(element, element.parent)
      element.parent.children.push(elementCopy)
      this.trigger("updateElements", [element.parent])
      this.trigger("closeContextMenu")
      this.startElementOrChildEditing(elementCopy)
      this.history.addState()
   }

   removeAllChildren(element){
      element.children = []
      this.trigger("updateElements", [element])
      this.history.addState()
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
               console.log(scrollTop)
            }
         }
      }
   }

   isElementDuplicationAllowed(element){
      return element.name != this.data.rootElement
            && !!element.parent
            && this.getAvailableChildElements(element.parent).includes(element.name)
   }

   isElementRemovalAllowed(element){
      if(element.name == this.data.rootElement){
         return false
      }
      let config = this.getElementConfig(element.name)
      if(config){
         let actualNumberOfElements = this.findElements(e => e.name == element.name, element.parent).length
         return element.name != this.data.rootElement
               && (!config.min || config.min < actualNumberOfElements)
      }
      return true
   }

   validateElement(element){
      if(element == this.data.detachedEntry || this.isServiceElement(element.name)){
         element.warnings = []
         element.isValid = true
      } else {
         let config = this.getElementConfig(element.name)
         let warnings = []
         if(!config || !config.type){  // has valid configuration
            warnings.push(`Unknown element "${element.name}".`)
         } else {
            if(config.type == "empty"){
               if(element.value){
                  warnings.push(`Element "${element.name}" should not have any text.`)
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
               counts[e.name] = counts[e.name] ? counts[e.name] + 1 : 1
               return counts
            }, {})
            config.children.forEach(childName => {
               let childConfig = this.getElementConfig(childName)
               if(childConfig){
                  if (childConfig.max && (counts[childName] || 0) > childConfig.max){
                     warnings.push(`Element "${element.name}" should have at most ${childConfig.max} "${childName}"`)
                  }
                  if (childConfig.min && (counts[childName] || 0) < childConfig.min){
                     warnings.push(`Element "${element.name}" should have at least ${childConfig.min} "${childName}"`)
                  }
               }
            })
            element.children.forEach(child => {
               if(!this.isServiceElement(child.name)){
                  if(!window.store.data.config.structure.elements[child.name]){
                     warnings.push(`'${element.name}' has unknown child element '${child.name}'.`)
                  } else if(!config.children.includes(child.name)){
                     warnings.push(`'${element.name}' must not have '${child.name}' as child element.`)
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

   validateNVHSchema(schema){
      if(schema && schema.trim()){
         try{
            let entry = this.nvhToJson(schema)
            let elementList = this.getElementList(entry)
            elementList.forEach(element => {
               window.structureEditorStore.validateElementName(element.name)
               if(elementList.filter(element2 => element.path == element2.path).length > 1){
                  throw `Element "${element.parent}" has two "${element.name}" elements.`
               }

               if(!this.parseNvhSchemaOptionsValue(element.value)){
                  throw `Element "${element.name}"" has invalid options: ${element.value}.`
               }
            })
         } catch (e){
            return {
               isValid: false,
               error: e
            }
         }
      }
      return {isValid: true}
   }

   parseNvhSchemaOptionsValue(value){
      //let re = new RegExp(/^(?<count>([\*\?\+]|\d+\+|\d+-\d+|\d+)?)\s*(?<type>(int|image|bool|audio|empty|url|string|list)?)\s*(?<values>(\[\s*"[^"]*"(\s*,\s*"[^"]*")*\s*\])?)\s*(?<regex>(~.*?)?)$/gm)
      let num = "\\d+"
      let space = "\\s*"
      let types = Object.keys(window.store.const.ENTRY_TYPES).join("|")
      let re = new RegExp(`^${space}(?<count>([\\*\\?\\+]|${num}\\+|${num}-${num}|${num})?)${space}`
                   + `(?<type>(${types})?)${space}`
                   + `(?<values>(\\[${space}"[^"]*"(${space},${space}"[^"]*")*${space}\\])?)${space}`
                   + `(?<regex>(~.*?)?)${space}$`)
      let parsed = re.exec(value)
      if(!parsed){
         return null
      } else {
         let min = 0
         let max = null
         if(parsed.groups.count == "?"){
            max = 1
         } else if(parsed.groups.count == "+"){
            min = 1
         } else if(parsed.groups.count.indexOf("-") != -1){
            let tmp = parsed.groups.count.split("-")
            min = tmp[0]
            max = tmp[2]
         } else{
            let num = parseInt(parsed.groups.count)
            if(!isNaN(num)){
               min = num
               max = num
            }
         }
         return {
            min: min,
            max: max,
            type: parsed.groups.type,
            values: parsed.groups.values.length
                        ? parsed.groups.values.slice(1,-1) // remove [ and  ]
                              .split(",")
                              .map(v => v.slice(1,-1))  // remove quotes
                        : null,
            regex: parsed.groups.regex
         }
      }
   }

   _getNewElementId(){
       // needed for riot to track changes properly
      return Math.round(Math.random() * 1000000)
   }

   _getElementDefaultValue(elementName){
      let config = this.getElementConfig(elementName)
      if(config){
         if(config.type == "empty"){
            return null
         } else if(config.type == "bool"){
            return 0
         } else if(config.type == "list" && config.values.length){
            return config.values[0]
         }
      }
      return ""
   }

   _getNewEntry(){
      let entry
      if(store.data.config.structure.custom_newEntryTemplate){
         entry = this.nvhToJson(store.data.config.structure.custom_newEntryTemplate)
      } else {
         entry = {
            id: this._getNewElementId(),
            name: this.data.rootElement,
            parent: null,
            indent: 0,
            value: "",
            children: []
         }
         this.addAllChildren(entry)
      }
      return entry
   }

   history = {
      records: [],
      actualIdx: 0,
      lastSavedIdx: 0,
      addState: () => {
         if(!this.history.records.length ||
            (this.jsonToNvh(this.data.entry) != this.jsonToNvh(this.history.records[this.history.actualIdx]))){
            if(this.history.actualIdx < this.history.records.length - 1){
               this.history.records.splice(this.history.actualIdx + 1)
            }
            this.history.records.push(this.copyElementAndItsChildren(this.data.entry))
            this.history.actualIdx = this.history.records.length - 1
            this.trigger("historyChanged")
         }
      },
      undo: () => {
         if(this.history.actualIdx > 0){
            this.history.actualIdx--
            this.data.entry = this.copyElementAndItsChildren(this.history.records[this.history.actualIdx])
            //this.data.sourceCode = null
            this.trigger("updateEditor")
            this.trigger("historyChanged")
         }
      },
      redo: () => {
         if(this.history.actualIdx < this.history.records.length - 1){
            this.history.actualIdx++
            this.data.entry = this.copyElementAndItsChildren(this.history.records[this.history.actualIdx])
            //this.data.sourceCode = null
            this.trigger("updateEditor")
            this.trigger("historyChanged")
         }
      },
      reset: () => {
         this.history.records = []
         this.history.actualIdx = 0
         this.history.lastSavedIdx = 0
      }
   }

   updateUrl(){
      let dictData = window.store.data
      let newUrl = `${window.location.href.split("#")[0]}#/${dictData.dictId}/edit/${dictData.doctype}/`
      if(dictData.entryId != null){
         newUrl += `${dictData.entryId}/${window.store.data.editorMode}${window.store.getEntrySearchUrlQueryString()}`
      }
      if(newUrl != window.location.href){
         history.pushState(null, null, newUrl)
         route.base() // need to update route's "current" value in
                       //order to browser back button works correctly
      }
   }

   escapeXMLValue(str) {
      return String(str)
            .replace(/&/g, "&amp;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&apos;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
   }

   unescapeXMLValue(value) {
      return String(value)
           .replace(/&quot;/g, "\"")
           .replace(/&apos;/g, "'")
           .replace(/&lt;/g, "<")
           .replace(/&gt;/g, ">")
           .replace(/&amp;/g, "&")
   }

   replaceMarkupOccurrences(value, element, createReplaceString) {
      let replaceList = []
      element.children.filter(child => {
         let config = this.getElementConfig(child.name)
         return !this.isServiceElement(child.name)
               && config && config.type == "markup"
      })
            .forEach(child => {
               let tmp = child.value.split("#")
               let find = tmp[0]
               if(find.trim()){
                  let replaceWith = createReplaceString(child.name, find)
                  if(child.value.indexOf("#") == -1){
                     replaceList.push({
                        index: value.indexOf(find),
                        find: find,
                        replaceWith: replaceWith
                     })
                  } else {
                     let occurrenceIndex = tmp[1]
                     let regex = new RegExp(window.reEscape(find), 'g');
                     let matches = Array.from(value.matchAll(regex))
                     if(matches.length >= occurrenceIndex) {
                        replaceList.push({
                           index: matches[occurrenceIndex - 1].index,
                           find: find,
                           replaceWith: replaceWith
                        })
                     }
                  }
               }
            })
      replaceList.sort((a, b) => {
         return b.index - a.index
      }).forEach(replaceObj => {
         // Replace occurrences from the end of the so the indexes will be still valid after each replacing.
         // Using indexes and backward replacing to avoid matches in already replaced strings (ie. search for "an"
         // would match "an" in "span" if previous "an" was already replaced with <span class="x">an</span>)
         value = value.slice(0, replaceObj.index) + replaceObj.replaceWith + value.slice(replaceObj.index + replaceObj.find.length)
      })
      return value
   }

   getElementTreeList(elementPath, indent=0){
      let list = []
      elementPath = elementPath || this.data.rootElement
      let elementConfig = this.data.structure.elements[elementPath]
      list.push({
         path: elementPath,
         elementName: elementConfig.name,
         color: this.getElementColor(elementPath),
         indent: indent
      })
      elementConfig && elementConfig.children.forEach(childName => {
         list.push(...this.getElementTreeList(childName, indent + 1))
      })
      return list
   }

   getElementColor(elementPath){
      let elIdx = Object.keys(this.data.structure.elements).indexOf(elementPath)
      return this.getColorByIndex(elIdx)
   }

   getColorByIndex(idx){
      return [
         "#3366cc",
         "#dc3912",
         "#ff9900",
         "#109618",
         "#990099",
         "#0099c6",
         "#dd4477",
         "#66aa00",
         "#b82e2e",
         "#316395",
         "#994499",
         "#22aa99",
         "#aaaa11",
         "#6633cc",
         "#e67300",
         "#8b0707",
         "#651067",
         "#329262",
         "#5574a6",
         "#3b3eac",
         "#b77322",
         "#16d620",
         "#b91383",
         "#f4359e",
         "#9c5935",
         "#a9c413",
         "#2a778d",
         "#668d1c",
         "#bea413",
         "#0c5922",
         "#743411"
      ][idx % 30] || "#000"
   }
}

window.nvhStore = new NVHStoreClass()
