class HistoryClass{
   constructor(){
      this.states = []
      this.actualIdx = 0
      observable(this)
   }

   getActualState(){
      return this.states[this.actualIdx]
   }

   addState(state){
      if(!this.states.length ||
         (state != this.states[this.actualIdx])){
         if(this.actualIdx < this.states.length - 1){
            this.states.splice(this.actualIdx + 1)
         }
         this.states.push(state)
         this.actualIdx = this.states.length - 1
         this.trigger("stateAdd")
         this.trigger("change")
      }
   }

   undo(){
      this.goTo(this.actualIdx - 1)
   }

   redo(){
      this.goTo(this.actualIdx + 1)
   }

   goTo(idx){
      if(idx >= 0 && idx <= this.states.length - 1){
         this.actualIdx = idx
         this.trigger("stateChange", this.actualIdx, this.states[this.actualIdx])
         this.trigger("change")
      }
   }

   reset(){
      this.states = []
      this.actualIdx = 0
      this.trigger("change")
   }
}

window.HistoryClass = HistoryClass
