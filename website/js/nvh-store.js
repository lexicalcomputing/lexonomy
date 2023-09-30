class NVHStoreClass {
   constructor(){
      this.lastId = 0
      this.const = {
         markDownNewLine: "<BR>"  //TODO
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
         rootElement: null,
         editorMode: "edit",
      }
      observable(this)
      window.store.on("dictionaryChanged", this.onDictionaryChanged.bind(this))
      window.store.on("entryIdChanged", this.onEntryIdChanged.bind(this))
      window.store.on("entryChanged", this.onEntryChanged.bind(this))
      this.on("updateElements", this.validateElements.bind(this))
   }

   createNewEntry(){
      this.data.revision && this.showRevision(null)
      this.closeRevisions()
      window.store.data.entryId = "new"
      this.data.entry = this._getNewEntry()
      this.validateAllElements()
      this.history.reset()
      this.history.addState()
      this.trigger("entryChanged")
      this.updateUrl()
   }

   saveEntry(){
      this.data.isSaving = true
      this.trigger("isSavingChanged")
      let nvh = this.jsonToNvh(this.data.entry)
      if(window.store.data.entryId != "new"){
         return window.store.updateEntry(nvh)
               .always(response => {
                  if(response.success){
                     M.toast({html: "Entry updated"})
                  } else {
                     M.toast({html: `Entry was not updated: ${response.feedback}`})
                  }
                  this.data.isSaving = false
                  this.trigger("isSavingChanged")
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
               window.store.data.entryId = response.entryId
               this.history.reset()
               this.history.addState()
               this.updateUrl()
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
      return $.ajax({
         url: `${window.API_URL}${window.store.data.dictId}/configupdate.json`,
         method: 'POST',
         data: {
            id: "xemplate",
            content: JSON.stringify(this.data.xemplate)
         }
      })
   }

   onDictionaryChanged(){
      this.data.structure = window.store.data.config.structure
      this.data.xemplate = window.store.data.config.xemplate
      this.data.editing = window.store.data.config.editing
      this.data.rootElement = this.data.structure.root
      this.data.customEditor = null
      this.data.legacyCustomEditor = false
      if(this.data.editing._js){
         try{
            let customEditor = new Function("return " + this.data.editing._js)();
            if(customEditor.editor && customEditor.harvester){
               this.data.customEditor = customEditor
               this.data.legacyCustomEditor = true
            } else if(customEditor.editor && customEditor.getValue){
               this.data.customEditor = customEditor
            } else{
               M.toast({html: "Invalid custom editor."})
            }
         } catch(e){
            M.toast({html: "Invalid custom editor code."})
         }
      }
   }

   onEntryIdChanged(){
      window.store.data.entryId == "new" && this.onEntryChanged()
   }

   onEntryChanged(){
      if(window.store.data.entryId == "new"){
         this.data.entry = this._getNewEntry()
      } else {
         this.data.entry = this.nvhToJson(window.store.data.entry.nvh)
      }
      this.validateAllElements()
      this.data.storedEntry = null
      this.data.revision = null
      this.data.editorMode = window.store.data.mode // TODO better initialization
      this.history.reset()
      this.history.addState()
      this.updateUrl()
      this.trigger("entryChanged")
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
      this.history.addState()
      this.closeRevisions()
      this.trigger("updateEditor")
   }

   parseNvhLine(line, idx, lastIndent){
      if(!line.match(new RegExp("^(([ ]{2})*)([a-zA-Z0-9-_]+):(.*)$"))){
         throw `Syntax error on line ${idx + 1}: '${line.trim()}'`
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

   jsonToNvh(element, indent=0){
      let nvh = `${" ".repeat(indent * 2)}${element.name}: ${element.value === null ? "" : element.value.replaceAll("\n", this.const.markDownNewLine)}\n`
      element.children.forEach(child => {
         nvh += this.jsonToNvh(child, indent + 1)
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
            el = {
               id: this._getNewElementId(),
               name: line.name,
               value: line.value.replaceAll(this.const.markDownNewLine, "\n"),
               indent: line.indent,
               parent: getParent(line.indent),
               children: [],
               warnings: []
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
      let addElementAndChildren = (element) => {
         if(!ret[element.name]){
            ret[element.name] = {
               name: element.name,
               children: [],
               type: "inl",
               warnings: []
            }
         }
         if(element.parent){
            ret[element.parent.name].type = "chd"
            ret[element.parent.name].children.push({
               name: element.name,
               min: ["", "+"].includes(element.value) ? 1 : 0, // * ? +
               max: ["", "?"].includes(element.value) ? 1 : 0
            })
         }
         element.children.forEach(addElementAndChildren)
      }
      let ret = {}
      addElementAndChildren(this.nvhToJson(nvhSchema))
      return ret
   }

   nvhSchemaToNvh(nvhSchema){
      let nvh = ""
      let json = this.nvhSchemaToJSON(nvhSchema)
      let addElementAndChildren = (element, indent) => {
         nvh += `${" ".repeat(indent * 2)}${element.name}:\n`
         element.children.forEach(child => {
            if(child.min){
               addElementAndChildren(json[child.name], indent + 1)
            }
         })
      }
      addElementAndChildren(json[nvhSchema.split(":", 1)[0]], 0)

      return nvh
   }

   changeEditorMode(mode){
      if(this.data.editorMode != mode){
         if(this.data.editorMode == "view" && this.data.customEditor){
            if(this.data.legacyCustomEditor){
               let entry = this.XMLToJson(this.data.customEditor.harvester())
               if(this.jsonToNvh(this.data.entry) != this.jsonToNvh(entry)){
                  this.entry = entry
                  this.history.addState()
               }
            } else {
               this.data.entry = this.nvhToJson(this.data.customEditor.getValue())
            }
            this.validateAllElements()
         }
         // TODO merge and use only one mode
         this.data.editorMode = mode
         window.store.data.mode = mode
         this.trigger("editorModeChanged")
         this.updateUrl()
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

   getElementList(element, list=[]){
      element = element || this.data.entry
      list.push(element)
      element.children.forEach(child => {
         this.getElementList(child, list)
      }, this)
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
      return this.data.structure.elements[elementName] || {}
   }

   getElementStyle(elementName){
      return this.data.xemplate[elementName] || {}
   }

   getAvailableChildElements(element){
      let config = this.data.structure.elements[element.name] || {}
      let elements = []
      if(config){
         elements = config.children.filter(c => {
            return this.canHaveAnotherChild(element, c.name)
         })
               .map(c => c.name)
      }
      return elements
   }

   canHaveAnotherChild(element, childName){
      let config = this.data.structure.elements[element.name].children.find(c => c.name == childName)
      return !config.max || config.max > element.children.filter(c => c.name == childName).length
   }

   getAvailableParentElementNames(element){
      let elements = this.data.structure.elements
      return Object.keys(elements).filter(elementName => {
         return elements[elementName].children.some(c => c.name == element.name)
      })
   }

   getAvailableParentElements(element){
      let availableParentNames = this.getAvailableParentElementNames(element)
      return this.findElements(parent => {
         return availableParentNames.includes(parent.name)
      })
   }

   getNextAvailableParentInDirection(element, direction){
      let availableParents = this.getAvailableParentElements(element)
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
         if(!value){
            delete this.data.xemplate[elementName][option]
         } else {
            this.data.xemplate[elementName][option] = value
         }
         this.saveStyle()
         this.trigger("updateElements", this.findElements(e => e.name == elementName))
      }
   }

   _moveChildToAnotherParent(child, newParent, position=null){
      // TODO opravit nazvy funkci aby byly konzistentni
      let idx = child.parent.children.indexOf(child)
      child.parent.children.splice(idx, 1)
      child.parent = newParent
      if(position === null){
         newParent.children.push(child)
      } else {
         newParent.children.splice(position, 0, child)
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

   copyElementAndItsChildren(element, parent=null){
      let copy = {
         id: Math.round(Math.random() * 1000000),
         parent: parent,
         children: [],
         warnings: []
      }
      Object.entries(element).forEach(obj => {
         if(obj[0] == "children"){
            obj[1].forEach(c => {
               copy.children.push(this.copyElementAndItsChildren(c, copy))
            })
         } else if(obj[0] == "parent"){

         } else if(["edit", "focused"].includes(obj[0])) {
            copy[obj[0]] = false
         } else {
            copy[obj[0]] = obj[1]
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
   }

   goToNextElement(){
      this.focusElement(this.getNextElement(this.getFocusedElement(), true))
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
      if(!["chd", "emp"].includes(config.type)){  // element with value
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
         return !["chd", "emp"].includes(config.type)
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
      this.trigger("onDndStart")
   }

   stopElementDragging(){
      this.data.draggedElement = null
      this.trigger("onDndStop")
   }

   moveChildToAnotherParent(element, newParent, position=0){
      let oldParentReference = element.parent
      this._moveChildToAnotherParent(element, newParent, position)
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
      //TODO scroll into view
      let childIdx = element.parent.children.indexOf(element)
      let newChildIdx = childIdx + direction
      if(newChildIdx >= 0 && newChildIdx < element.parent.children.length){
         element.parent.children.splice(childIdx, 1)
         element.parent.children.splice(childIdx + direction, 0, element)
         this.trigger("updateElements", [element.parent])
         this.history.addState()
      }
   }

   moveElementToParentInDirection(element, direction){
      //TODO scroll into view
      let newParent = this.getNextAvailableParentInDirection(element, direction)
      if(newParent){
         let oldParentReference = element.parent
         this._moveChildToAnotherParent(element, newParent, direction == 1 ? 0 : null)
         this.makeElementVisible(element)
         this.trigger("updateElements", [oldParentReference, newParent])
         this.history.addState()
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
      config.children.forEach(childConfig => {
         if(childConfig.min > 0){
            Array.from({length: childConfig.min}).forEach(empty => {
               let childElement = this._addChildElement(element, childConfig.name)
               this.addRequiredChildren(childElement)
            })
         }
      })
   }

   addAllChildren(element){
      let config = this.getElementConfig(element.name)
      config.children.forEach(childConfig => {
         Array.from({length: childConfig.min || 1}).forEach(empty => {
            let childElement = this._addChildElement(element, childConfig.name)
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
      // TODO focus some element after removing active element, so user can work with keyboard
      let globalIdx = this.getElementList().indexOf(element)
      let childIdx = element.parent.children.findIndex(e => e == element)
      element.parent.children.splice(childIdx, 1)
      let nextElement = this.getElementList()[globalIdx]
      nextElement && this.forEachElement(e => {e.focused = e == nextElement})
      this.trigger("updateElements", [element.parent])
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

   isElementDuplicationAllowed(element){
      return element.name != this.data.rootElement
            && this.getAvailableChildElements(element.parent).includes(element.name)
   }

   isElementRemovalAllowed(element){
      if(element.name == this.data.rootElement){
         return false
      }
      let minimumNumberOfElements = this.getElementConfig(element.parent.name).children.find(e => e.name == element.name).min
      let actualNumberOfElements = this.findElements(e => e.name == element.name, element.parent).length
      return element.name != this.data.rootElement
            && (!minimumNumberOfElements || minimumNumberOfElements > actualNumberOfElements)
   }

   validateElement(element){
      let config = this.getElementConfig(element.name)
      let warnings = []
      if(!config || !config.type){  // has valid configuration
         warnings.push(`Unknown element "${element.name}".`)
      } else {
         if(config.type == "emp"){
            if(element.children.length){
               warnings.push(`Element "${element.name}" should be empty but it contains other element.`)
            }
         } else if(config.type == "chd"){
            if(element.value){
               warnings.push(`Element "${element.name}" should not have any text.`)
            }
         } else if(config.type == "lst"){
            if(!element.value){
               warnings.push(`Element "${element.name}" should not be empty.`)
            } else if(!config.values.find(v => v.value == element.value)){
               warnings.push(`Element "${element.name}" should not have the value "${element.value}".`)
            }
         }
         if(["txt", "inl"].includes(config.type)){
            if(!element.value){
               warnings.push(`Element "${element.name}" should have some text.`)
            }
         }
         if(["chd", "inl"].includes(config.type)){
            let counts = element.children.reduce((counts, e) => {
               counts[e.name] = counts[e.name] ? counts[e.name] + 1 : 1
               return counts
            }, {})
            config.children.forEach(childConfig => {
               if (childConfig.max && (counts[childConfig.name] || 0) > childConfig.max){
                  warnings.push(`Element "${element.name}" should have at most ${childConfig.max} "${childConfig.name}"`)
               }
               if (childConfig.min && (counts[childConfig.name] || 0) < childConfig.min){
                  warnings.push(`Element "${element.name}" should have at least ${childConfig.min} "${childConfig.name}"`)
               }
            })
         }
         element.children.forEach(child => {
            if(!window.store.data.config.structure.elements[child.name]){
               warnings.push(`'${element.name}' has unknown child element '${child.name}'.`)
            }
            if(!config.children.map(c => c.name).includes(child.name)){
               warnings.push(`'${element.name}' must not have '${child.name}' as child element.`)
            }
         })
      }

      element.warnings = warnings
      element.isValid = !warnings.length
      let isValid = !this.findElement(e => !e.isValid)
      if(this.data.isValid != isValid){
         this.data.isValid = isValid
         this.trigger("isValidChanged")
      }
   }

   validateElements(elements){
      elements.forEach(this.validateElement.bind(this))
   }

   validateAllElements(){
      this.forEachElement(this.validateElement.bind(this))
   }

   parseMarkDown(md){
      if(!md){
         return md
      }
         //ul
      return md.replace(/^\s*\n\*/gm, '<ul>\n*')
         .replace(/^(\*.+)\s*\n([^\*])/gm, '$1\n</ul>\n\n$2')
         .replace(/^\*(.+)/gm, '<li>$1</li>')
         //ol
         .replace(/^\s*\n\d\./gm, '<ol>\n1.')
         .replace(/^(\d\..+)\s*\n([^\d\.])/gm, '$1\n</ol>\n\n$2')
         .replace(/^\d\.(.+)/gm, '<li>$1</li>')
         //blockquote
         .replace(/^\>(.+)/gm, '<blockquote>$1</blockquote>')
         //h
         .replace(/[\#]{6}(.+)/g, '<h6>$1</h6>')
         .replace(/[\#]{5}(.+)/g, '<h5>$1</h5>')
         .replace(/[\#]{4}(.+)/g, '<h4>$1</h4>')
         .replace(/[\#]{3}(.+)/g, '<h3>$1</h3>')
         .replace(/[\#]{2}(.+)/g, '<h2>$1</h2>')
         .replace(/[\#]{1}(.+)/g, '<h1>$1</h1>')
         //alt h
         .replace(/^(.+)\n\=+/gm, '<h1>$1</h1>')
         .replace(/^(.+)\n\-+/gm, '<h2>$1</h2>')
         //images
         .replace(/\!\[([^\]]+)\]\(([^\)]+)\)/g, '<img src="$2" alt="$1" />')
         //links
         .replace(/[\[]{1}([^\]]+)[\]]{1}[\(]{1}([^\)\"]+)(\"(.+)\")?[\)]{1}/g, '<a href="$2" title="$4">$1</a>')
         //font styles
         .replace(/[\*]{2}([^\*]+)[\*]{2}/g, '<b>$1</b>')
         .replace(/[\_]{1}([^\_]+)[\_]{1}/g, '<i>$1</i>')
         .replace(/[\~]{2}([^\~]+)[\~]{2}/g, '<del>$1</del>')
         //pre
         .replace(/^\s*\n\`\`\`(([^\s]+))?/gm, '<pre class="$2">')
         .replace(/^\`\`\`\s*\n/gm, '</pre>\n\n')
         //code
         .replace(/[\`]{1}([^\`]+)[\`]{1}/g, '<code>$1</code>')
         //p
         .replace(/^\s*(\n)?(.+)/gm, function(m){
            return  /\<(\/)?(h\d|ul|ol|li|blockquote|pre|img)/.test(m) ? m : m+'<br>';
         })
         //strip p from pre
         .replace(/(\<pre.+\>)\s*\n\<p\>(.+)\<\/p\>/gm, '$1$2')
         //remove trailing <br>
         .replace(/[\<br\>]*$/,"")
   }

   _getNewElementId(){
       // needed for riot to track changes properly
      return Math.round(Math.random() * 1000000)
   }

   _getElementDefaultValue(elementName){
      let config = this.getElementConfig(elementName)
      let type = config.type
      if(["chd", "emp"].includes(type)){
         return null
      } else if(type == "lst"){
         return config.values[0].value
      }
      return ""
   }

   _getNewEntry(){
      let entry
      if(store.data.config.structure._newEntryNvh){
         entry = this.nvhToJson(store.data.config.structure._newEntryNvh)
      } else {
         entry = {
            id: this._getNewElementId(),
            name: this.data.rootElement,
            parent: null,
            indent: 0,
            value: null,
            children: []
         }
         this.addAllChildren(entry)
      }
      return entry
   }

   history = {
      records: [],
      actualIdx: 0,
      addState: () => {
         if(!this.history.records.length ||
            (this.jsonToNvh(this.data.entry) != this.jsonToNvh(this.history.records[this.history.actualIdx]))){
            if(this.history.actualIdx < this.history.records.length - 1){
               this.history.records.splice(this.history.actualIdx)
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
         }
         this.trigger("updateEditor")
         this.trigger("historyChanged")
      },
      redo: () => {
         if(this.history.actualIdx < this.history.records.length - 1){
            this.history.actualIdx++
            this.data.entry = this.copyElementAndItsChildren(this.history.records[this.history.actualIdx])
            //this.data.sourceCode = null
         }
         this.trigger("updateEditor")
         this.trigger("historyChanged")
      },
      reset: () => {
         this.history.records = []
         this.history.actualIdx = 0
      }
   }

   updateUrl(){
      let dictData = window.store.data
      let newUrl = `${window.location.href.split("#")[0]}#/${dictData.dictId}/edit/${dictData.doctype}/`
      if(dictData.entryId != null){
         newUrl += `${dictData.entryId}/${this.data.editorMode}${url.stringifyQuery(route.query())}`
      }
      if(newUrl != window.location.href){
         history.pushState(null, null, newUrl)
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

   getElementColor(elementName){
      let elIdx = Object.keys(this.data.structure.elements).indexOf(elementName)
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
