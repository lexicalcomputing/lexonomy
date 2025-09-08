class NvhSchemaClass{
   constructor(nvh=""){
      observable(this)
      this.update(nvh)
   }

   update(nvh){
      this.nvh = nvh
      try{
         this.schema = this.parseNvhSchema(nvh)
      } catch(e){
         this.schema = null
      }
      this._validate()
      this.trigger("schemaChanged")
   }

   findElement(callback){
      return this.getElementList().find(callback)
   }

   findElements(callback){
      return this.getElementList().filter(callback)
   }

   getElementList(){
      return this.jsonToList(this.schema)
   }

   forEach(callback, element){
      element = element || this.schema
      if(element){
         callback(element)
         element.children?.forEach(this.forEach.bind(this, callback))
      }
   }

   forEachChildren(element, callback){
      element.children?.forEach(child => {
         callback(child)
         this.forEachChildren(child, callback)
      })
   }

   isEmpty(){
      return !this.nvh
   }

   isPathRoot(elementPath){
      return this.getElementByPath(elementPath)?.indent == 0
   }

   isElementRoot(element){
      return element.indent == 0
   }

   getNvh(){
      return this.nvh
   }

   getRoot(){
      return this.schema
   }

   getElementByPath(elementPath){
      return this.findElement(element => element.path == elementPath)
   }

   getElementColor(element){
      let idx = this.getElementList().indexOf(element)
      return window.getColorByIndex(idx)
   }

   getPathColor(elementPath){
      let idx = this.getElementList()
            .findIndex(element => element.path == elementPath)
      return window.getColorByIndex(idx)
   }

   getAllElementAncestors(element){
      let ancestors = []
      while (element.parent) {
         ancestors.push(element.parent)
         element = element.parent
      }
      return ancestors
   }

   getElementCountString(element){
      let min = element.min
      let max = element.max
      let str
      if(min > 0){
         if(max > 0){
            if(min == max){
               return `${min}×`
            } else {
               return `${min}–${max}×`
            }
         } else {
            return `at least ${min}×`
         }
      } else if(max > 0){
         return `at most ${max}×`
      }
      return ""
   }

   addChildElement(parentElement, childElement, position=0){
      childElement.path = parentElement ? `${parentElement.path}.${childElement.name}` : childElement.name,
      childElement.children ??= []
      childElement.parent = parentElement
      childElement.indent = childElement.path.split(".").length - 1
      if(!parentElement){
         this.schema = childElement
      } else {
         if(typeof position == "undefined"){
            parentElement.children.push(childElement)
         } else {
            parentElement.children.splice(position, 0, childElement)
         }
      }
      this._refreshNvh()
      this._validate()
      this.trigger("schemaChanged")
   }

   updateElement(element, changes){
      if(changes.name){
         element.name = changes.name
         this.forEachChildren(element, child => child.path = `${child.parent.path}.${child.name}`)
      }
      Object.assign(element, changes)
      this._refreshNvh()
      this._validate()
      this.trigger("schemaChanged")
   }

   removeElement(element){
      if(element.parent){
         let childIdx = element.parent.children.findIndex(e => e == element)
         element.parent.children.splice(childIdx, 1)
      } else {
         this.schema = null
      }
      this._refreshNvh()
      this._validate()
      this.trigger("schemaChanged")
   }

   moveElementToAnotherParent(element, newParent, position=0){
      let idx = element.parent.children.indexOf(element)
      if(element.parent == newParent && idx < position){
         position--
      }
      element.parent.children.splice(idx, 1)
      element.parent = newParent
      element.path = `${newParent.path}.${element.name}`
      element.indent = newParent.indent + 1
      newParent.children.splice(position, 0, element)
      this.forEachChildren(element, child => {
         child.path = `${child.parent.path}.${child.name}`
         child.indent = child.parent.indent + 1
      })
      this._refreshNvh()
      this._validate()
      this.trigger("schemaChanged")
   }

   jsonToList(json){
      let list = []
      let addElementAndItsChildren = element => {
         if(element){
            list.push(element)
            element.children.forEach(childElement => {
               addElementAndItsChildren(childElement)
            })
         }
      }
      addElementAndItsChildren(json)
      return list
   }

   validateElementName(elementName){
      if(!elementName){
         throw "Please, enter element name."
      } else if(!/^[a-zA-Z10-9_-]+$/.test(elementName)){
         throw `Invalid element name '${elementName}'. Allowed characters: a-Z, A-Z, 0-9, _ and -.`
      } else if(["and", "or"].includes(elementName.toLowerCase())){
         throw "'AND' and 'OR' are not allowed element names."
      }
   }

   stringifyElement(element){
      let count = ""
      let regex = ""
      let values = ""
      if(!element.max){
         if(element.min == 1){
            count = " +"
         } else if (element.min > 1){
            count = ` ${element.min}+`
         } else {
            count = " *"
         }
      } else {
         if(element.max == 1 && !element.min){
            count = " ?"
         } else {
            if(element.min == element.max){
               count = ` ${element.min}`
            } else {
               count = ` ${element.min || 0}-${element.max}`
            }
         }
      }
      if(element.re){
         regex = ` ~${element.re}`
      }
      if(element.type == "list" && element.values && element.values.length){
         values = ` [${element.values.map(value => `"${value}"`).join(",")}]`
      }
      return `${" ".repeat(element.indent * 2)}${element.name}:${count} ${element.type}${values}${regex}`
   }

   parseNvhSchema(nvhSchema){
      let json = window.nvhStore.nvhToJson(nvhSchema)
      this.forEach(element => {
         let options = this.parseOptionsValue(element.value)
         if(!options){
            throw `Element "${element.name}" has invalid options: ${element.value}.`
         }
         Object.assign(element, options)
      }, json)
      return json
   }

   parseOptionsValue(value){
      let num = "\\d+"
      let space = "\\s*"
      let types = Object.keys(window.store.const.ENTRY_TYPES).join("|")
      let re = new RegExp(`^${space}(?<count>([\\*\\?\\+]|${num}\\+|${num}-${num}|${num})?)${space}`
                   + `(?<type>(${types})?)${space}`
                   + `(?<values>(\\[${space}"[^"]*"(${space},${space}"[^"]*")*${space}\\])?)${space}`
                   + `(?<re>(~.*?)?)${space}$`)
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
            [min, max] = parsed.groups.count.split("-")
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
            type: parsed.groups.type || "string",
            values: parsed.groups.values ? JSON.parse(parsed.groups.values) : [],
            re: parsed.groups.re ? parsed.groups.re.slice(1) : ""  // remove ~
         }
      }
   }

   _validate(){
      let oldError = this.error
      this.parseError = null
      this.error = false
      if(this.nvh && this.nvh.trim()){
         let json
         try{
            json = this.parseNvhSchema(this.nvh)
         } catch (e){
            this.error = e
            this.parseError = true
         }
         try{
            let elementList = this.jsonToList(json)
            elementList.forEach(element => {
               this.validateElementName(element.name)
               if(elementList.filter(element2 => element.path == element2.path).length > 1){
                  throw `Element "${element.parent.name}" has two "${element.name}" elements.`
               }
               if(element.parent && element.parent.type == "markup"){
                  if(element.children.length){
                     throw `Element "${element.name}" should not have any children, because its parent type is "Text markup".`
                  }
                  if(element.max != 1){
                     throw `Element "${element.name}" must have Max set to 1, because its parent type is "Text markup".`
                  }
                  if(element.max > 1){
                     throw `Element "${element.name}" must have Min set to 0 or 1, because its parent type is "Text markup".`
                  }
                  if(["markup", "empty"].includes(element.type)){
                     throw `Element "${element.name}" must not have type ${window.store.const.ENTRY_TYPES[options.type]}, because its parent type is "Text markup".`
                  }
                  if(element.re){
                     try{
                        new RegExp(element.re)
                     } catch(e){
                        throw `Element "${element.name}" has invalid regular expression.`
                     }
                  }
               }
            })
         } catch(e){
            this.error = e
         }
      }
      this.isValid = !this.error
      if(oldError != this.error){
         this.trigger("isValidChanged")
      }
   }

   _refreshNvh(){
      if(this.schema){
         try{
            let elementToNvh = (element) => {
               let rows = []
               rows.push(this.stringifyElement(element))
                  element.children && element.children.forEach(child => {
                  rows.push(elementToNvh(child))
               }, this)
               return rows.join("\n")
            }
            this.nvh = elementToNvh(this.schema)
         } catch(e){}
      }
   }
}

window.NvhSchemaClass = NvhSchemaClass
