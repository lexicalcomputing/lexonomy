{
editor: function(options) {
 // options = {
 //   node: the node into which you should render the editor
 //   entry = JSON object representing the entry
 //   readOnly = true if we want the entry to be uneditable
 //   onChange = the method should be called if the data is changed
 //   onValidChange - the method should be called if data state changes from valid to invalid or vice versa
 //   destroy - this method is called when the editor is closed
 // }
 this.options = options
 this.node = $(options.node)
 this.entry = options.entry
 let editorNode = $("<div class='myEditor'><h3>My custom editor</h3></div>").appendTo(this.node)
 this.contentNode = $('<div class="myEditorContentNode"></div>').appendTo(editorNode)
 this.isValid = null
 this._render()
 this._validate()
},

getValue: function() {
 return {
    name: "entry",
    value: this.contentNode.find("input.headword").val(),
    children: [{
       name: "partOfSpeech",
       value: this.contentNode.find("input.partOfSpeech").val()
    }]
 }
},

update: function(entry) {
 this.entry = entry
 this._render()
 this._validate()
},

_render: function() {
 this.contentNode.empty()
 $(`<label>headword</label>`).appendTo(this.contentNode)
 $(`<input class="headword"
       ${this.options.readOnly? "disabled" : ""}
       value="${this.entry.value}"/>`)
       .appendTo(this.contentNode)
       .on("input", this._onInput.bind(this))
       .on("change", this.options.onChange)
 $(`<label>Part of speech</label>`).appendTo(this.contentNode)
 $(`<input class="partOfSpeech"
       ${this.options.readOnly? "disabled" : ""}
       value="${window.nvhStore.findElement(e => e.name == "partOfSpeech").value}"/>`)
       .appendTo(this.contentNode)
       .on("input", this._onInput.bind(this))
       .on("change", this.options.onChange)
},

_onInput: function() {
 this._validate()
},

_validate: function() {
 let wasValid = this.isValid
 this.isValid = this.contentNode.find("input.headword").val() !== ""
       && this.contentNode.find("input.partOfSpeech").val() !== ""
 if (wasValid != this.isValid) {
    this.options.onValidChange(this.isValid)
 }
}
}
