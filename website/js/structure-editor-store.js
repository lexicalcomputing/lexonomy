class StructureEditorStoreClass {
   constructor(){
      this.reset()
      observable(this)
   }

   reset(){
      this.data = {
         structure: {
            elements: {},
            root: null
         },
         draggedElement: null,
         editedElement: null
      }
   }

   setConfigStructure(structure){
      this.data.structure = structure
      // TODO mabye do on backend
      Object.entries(structure.elements).forEach(([path, element]) => {
         element.path = path
         element.indent = path.split(".").length - 1
         element.children = element.children || []
         element.parent = element.path.split(".").slice(0, -1).join(".") || null
      })
   }

   nvhToStructure(nvh){
      let jsonSchema = window.nvhStore.nvhSchemaToJSON(nvh)
      let elements = {}
      let addElement = element => {
         elements[element.path] = {
            name: element.name,
            path: element.path,
            children: element.children.map(childElement => childElement.path),
            indent: element.indent,
            type: element.type || "string",
            max: element.max,
            min: element.min,
            re: element.re,
            values: element.values
         }
         element.children.forEach(addElement)
      }
      addElement(jsonSchema)

      return {
         elements: elements,
         root: jsonSchema.name
      }
   }

   getElementByPath(elementPath){
      return this.data.structure.elements[elementPath] || null
   }

   getRootElement(){
      return this.getElementByPath(this.data.structure.root)
   }

   addElement(element){
      let rootElement = this.getRootElement()
      Object.assign(element, {
         indent: rootElement ? 1 : 0,
         parent: rootElement ? this.data.structure.root : null,
         path: rootElement ? `${this.data.structure.root}.${element.name}` : element.name,
         children: []
      })
      if(rootElement){
         rootElement.children.push(element.path)
      } else {
         this.data.structure.root = element.name
      }
      this.data.structure.elements[element.path] = element
      this.trigger("elementChanged")
   }

   updateElement(element){
      let ancestorNames = element.path.split(".")
      let oldElementName = ancestorNames.pop()  // element name could be changed, but path is still original
      if(oldElementName != element.name){
         let oldElementPath = element.path
         let newElementPath = [...ancestorNames, element.name].join(".")
         this.changeElementPath(element, newElementPath)
         let parent = this.getElementByPath(element.parent)
         if(oldElementPath == this.data.structure.root){
            this.data.structure.root = element.name
         }
         if(parent){
            parent.children[parent.children.indexOf(oldElementPath)] = element.path
         }
      }
      this.trigger("elementChanged")
   }

   removeElement(element){
      let parent = this.getElementByPath(element.parent)
      if(parent){
         parent.children = parent.children.filter(child => child != element.path)
      }
      let deleteElementAndItsChildren = (element) => {
         element.children && element.children.forEach(childPath => {
            deleteElementAndItsChildren(this.getElementByPath(childPath))
         })
         delete this.data.structure.elements[element.path]
      }
      deleteElementAndItsChildren(element)

      if(element.path == this.data.structure.root){
         this.data.structure.root = null
      }

      this.trigger("elementChanged")
   }

   changeElementPath(element, newPath){
      if(newPath == element.path){
         return
      }
      let oldElementPath = element.path
      let childPaths = []
      element.children.forEach(childPath => {
         let newChildPath = `${newPath}.${childPath.split(".").pop()}`
         this.changeElementPath(this.getElementByPath(childPath), newChildPath)
         childPaths.push(newChildPath)
      })
      Object.assign(element, {
         path: newPath,
         parent: newPath.split(".").slice(0, -1).join("."),
         indent: newPath.split(".").length - 1,
         children: childPaths
      })
      this.data.structure.elements[newPath] = element
      delete this.data.structure.elements[oldElementPath]
   }

   moveElementToAnotherParent(childElement, newParentElement, position=0){
      let actualParent = this.getElementByPath(childElement.parent)
      actualParent.children = actualParent.children.filter(childPath => childPath != childElement.path)
      this.changeElementPath(childElement, `${newParentElement.path}.${childElement.name}`)
      if(position === null){
         newParentElement.children.push(childElement.path)
      } else {
         newParentElement.children.splice(position, 0, childElement.path)
      }
      this.trigger("elementChanged")
   }

   startElementEditing(element){
      this.data.editedElement = element
      this.trigger("elementChanged")
   }

   stopElementEditing(){
      if(this.data.editedElement){
         this.data.editedElement = null
         this.trigger("elementChanged")
      }
   }

   startElementDragging(element){
      this.data.draggedElement = element
      this.trigger("onDndStart")
   }

   stopElementDragging(){
      this.data.draggedElement = null
      this.trigger("onDndStop")
   }

   getNvh(){
      return this.jsonToNvh(this.data.structure)
   }

   jsonToNvh(structure){
      let ret = ""
      let elementToNvh = (elementPath, indent=0) => {
         let element = structure.elements[elementPath]
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
                  count = ` ${element.min}-${element.max}`
               }
            }
         }
         if(element.re){
            regex = ` ~${element.re}`
         }
         if(element.type == "list" && element.values && element.values.length){
            values = ` [${element.values.map(value => `"${value}"`).join(",")}]`
         }

         let rows = []
         rows.push(`${" ".repeat(indent * 2)}${element.name}:${count} ${element.type}${values}${regex}`)
            element.children && element.children.forEach(childPath => {
            rows.push(elementToNvh(childPath, indent + 1))
         }, this)
         return rows.join("\n")
      }
      return elementToNvh(structure.root)
   }

   getAllAncestors(elementPath){
      return this.getAllAncestorPaths(elementPath).map(this.getElementByPath.bind(this))
   }

   getAllAncestorPaths(elementPath){
      let ancestorNames = elementPath.split(".")
      return ancestorNames.map((ancestorName, idx) => {
         return ancestorNames.slice(0, idx + 1).join(".")
      })
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
}

window.structureEditorStore = new StructureEditorStoreClass()
