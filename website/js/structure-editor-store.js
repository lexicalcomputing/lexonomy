class StructureEditorStoreClass {
   constructor(){
      this.reset()
      observable(this)
   }

   reset(){
      this.const = {
         types: {
            string: "Text",
            int: "Number",
            image: "Image",
            audio: "Audio",
            url: "URL",
            empty: "Empty", // no value, just child elements
            bool: "Yes/No"
         }
      }
      this.data = {
         structure: {
            elements: {},
            root: null
         },
         draggedElement: null,
         basic_finalSchema: null,
         basic_modules: [],
         advanced_structure: {
            elements: {},
            root: null
         },
         custom_NVHSchema: "",
         custom_newEntryTemplate: ""
      }
   }

   setConfigStructure(structure){
      this.data.structure = structure
      Object.entries(structure.elements).forEach(obj => {
         obj[1].name = obj[0]
         obj[1].children = obj[1].children || []
      })
      this.refreshAllElementsIndent()
   }

   getElementByName(elementName){
      return this.data.structure.elements[elementName]
   }

   getRootElement(){
      return this.getElementByName(this.data.structure.root)
   }

   addElement(element){
      Object.assign(element, {
         indent: 1,
         children: []
      })
      this.data.structure.elements[element.name] = element
      let rootElement = this.getRootElement()
      if(rootElement){
         rootElement.children.push(element.name)
      } else {
         this.data.structure.root = element.name
      }
      this.refreshAllElementsIndent()
      this.trigger("elementChanged")
   }

   updateElement(elementName, element){
      Object.assign(this.data.structure.elements[elementName], element)
      if(elementName != element.name){
         if(elementName == this.data.structure.root){
            this.data.structure.root = element.name
         }
         this.forEachElement(el => {
            let idx = el.children.indexOf(elementName)
            if(idx != -1){
               el.children[idx] = element.name
            }
         })
         this.data.structure.elements[element.name] = this.data.structure.elements[elementName]
         delete this.data.structure.elements[elementName]
      }
      this.trigger("elementChanged")
   }

   removeElement(element){
      let parent = this.getParentElement(element.name)
      if(parent){
         parent.children = parent.children.filter(child => child != element.name)
      }
      let deleteElementAndItsChildren = (element) => {
         element.children && element.children.forEach(childName => {
            deleteElementAndItsChildren(this.getElementByName(childName))
         })
         delete this.data.structure.elements[element.name]
      }
      deleteElementAndItsChildren(element)

      if(element.name == this.data.structure.root){
         this.data.structure.root = null
      }

      this.trigger("elementChanged")
   }

   moveElementToAnotherParent(draggedElement, droppedToElement, indent){
      let actualParent = this.getParentElement(draggedElement.name)
      actualParent.children = actualParent.children.filter(childName => childName != draggedElement.name)
      this.forEachElement(e => {
         e.children = e.children.filter(child => child != draggedElement.name)
      })
      if(droppedToElement.indent < indent){
         // adding as child
         droppedToElement.children.unshift(draggedElement.name)
      } else if(droppedToElement.indent == indent){
         // adding as sibling
         let newParentElement = this.getParentElement(droppedToElement.name)
         let position = newParentElement.children.indexOf(droppedToElement.name)
         newParentElement.children.splice(position + 1, 0, draggedElement.name)
      }
      this.refreshAllElementsIndent()
      this.trigger("elementChanged")
   }

   startElementEditing(element){
      this.data.editedElement = element
      this.trigger("elementChanged")
   }

   stopElementEditing(){
      this.data.editedElement = null
      this.trigger("elementChanged")
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
      let ret = ""
      let elementToNvh = (element, indent=0) => {
         let count = ""
         let regex = ""
         let values = ""
         if(!element.max){
            if(element.min == 1){
               count = " +"
            } else if (element.min > 1){
               count = ` ${element.min}+`
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
         if(element.regex){
            regex = ` ~${element.regex}`
         }
         if(element.values && element.values.length){
            values = ` [${element.values.map(v => v.value).join(", ")}]`
         }

         let nvh = `${" ".repeat(indent * 2)}${element.name}: ${element.type}${count}${regex}${values}\n`
            element.children && element.children.forEach(childName => {
            nvh += elementToNvh(this.getElementByName(childName), indent + 1)
         }, this)
         return nvh
      }
      return elementToNvh(this.getRootElement())
   }

   forEachElement(callback){
      Object.values(this.data.structure.elements).forEach(callback)
   }

   getStructureToSave(){
      let elements = {}
      Object.values(this.data.structure.elements).forEach(element => {
         let el = Object.assign({}, element)
         delete el.indent
         delete el.name
         elements[element.name] = el
      })
      return {
         elements: elements,
         root: this.data.structure.root
      }
   }

   getAllAncestorNames(elementName){
      let actualElement = elementName
      let ancestors = []
      do {
         ancestors.unshift(actualElement)
         actualElement = this.getElementParentName(actualElement)
      } while(actualElement)
      return ancestors
   }

   getElementParentName(elementName){
      let element = this.getElementByName(elementName)
      for(let parentName in this.data.structure.elements){
         if(this.data.structure.elements[parentName].children && this.data.structure.elements[parentName].children.includes(elementName)){
            return parentName
         }
      }
      return null
   }

   getParentElement(elementName){
      return this.getElementByName(this.getElementParentName(elementName))
   }

   refreshAllElementsIndent(){
      let addElementAndItsChildren = (element, indent) => {
         element.indent = indent
         element.children.forEach(childName => {
            addElementAndItsChildren(this.getElementByName(childName), indent + 1)
         })
      }
      let rootElement = this.getRootElement()
      rootElement && addElementAndItsChildren(rootElement, 0)
   }
}

window.structureEditorStore = new StructureEditorStoreClass()
