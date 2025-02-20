class StructureEditorStoreClass {
   constructor(){
      this.data = {
         schema: null,
         tab: null,
         mode: null,
         originalSchema: null,
         originalDmlexSettings: null,
         draggedElement: null,
         editedElement: null
      }
      observable(this)
   }

   setSchema(schema){
      this.data.schema = schema
   }

   addElement(element){
      this.data.schema.addChildElement(element.parent, element)
      this.stopElementEditing()
      this.trigger("elementChanged")
   }

   deleteElement(element){
      this.data.schema.removeElement(element)
      this.stopElementEditing()
      this.trigger("elementChanged")
   }

   updateElement(element, changes){
      this.data.schema.updateElement(element, changes)
      this.stopElementEditing()
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
}

window.structureEditorStore = new StructureEditorStoreClass()
