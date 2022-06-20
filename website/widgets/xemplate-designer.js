class XemplateDesignerClass {
	constructor() {
		this.previewXml = "";
		this.xemplate = null
		this.dictID = null
	}

	start(xema, xemplate, dictID) { //the editor can be an HTML element, or the string ID of one.
		this.xemaDesigner = new window.XemaDesignerClass()
		this.xemaDesigner.xema = xema;
		this.xema = xema;
		this.xemplate = xemplate;
		this.dictID = dictID;
		if (typeof(editor) == "string") editor = document.getElementById(editor);
		var $editor = $("#editor").addClass("designer");
		$editor.append("<div class='list'></div><div class='details narrow'></div><div class='preview'></div>");
		this.xemaDesigner.renderElement = this.renderElement.bind(this);
		this.xemaDesigner.renderAttribute = this.renderAttribute.bind(this);
		this.xemaDesigner.listNodes();
		this.xemaDesigner.selectElement(xema.root);
		this.renderPreview();
	};

	onchange() {
		this.refreshPreview();
	};

	renderPreview() {
		var $details = $(".designer .preview").html("");
		var $block = $("<div class='block'></div>").appendTo($(".designer .preview"));
		var $title = $("<div class='title'>Preview</div>").appendTo($block)
		$title.append("<span class='reload'>reload random entry</span>").on("click", this.reloadPreviewXml.bind(this));
		var $area = $("<div class='area viewer'></div>").appendTo($(".designer .preview"));
		var $area = $("<div class='noentries' style='display: none'>The dictionary has no entries yet.</div>").appendTo($(".designer .preview"));
		this.reloadPreviewXml();
	};

	reloadPreviewXml() {
		$.ajax({
			url: window.API_URL + "/" + this.dictID + "/randomone.json",
			dataType: "json",
			method: "POST"
		}).done(function(data) {
			if (data.id > 0) {
				var doc = (new DOMParser()).parseFromString(data.xml, 'text/xml');
				this.previewXml = doc;
				this.refreshPreview();
				$(".designer .preview .area").hide().fadeIn();
			} else {
				$(".designer .preview .area").hide();
				$(".designer .preview .noentries").show();
			}
		}.bind(this));
	};

	refreshPreview() {
		var html = Xemplatron.xml2html(this.previewXml, this.xemplate, this.xema);
		var $details = $(".designer .preview .area").html(html);
	}

	getElementXemplate(elName) {
		if (!this.xemplate[elName]) {
			if (elName == this.xemaDesigner.xema.root) this.xemplate[elName] = {
				shown: false,
				layout: "block"
			};
			else this.xemplate[elName] = {
				shown: true,
				layout: "block"
			};
		}
		if (this.xemplate[elName].shown == "false") this.xemplate[elName].shown = false;
		return this.xemplate[elName];
	};

	getAttributeXemplate(elName, atName) {
		var x = this.getElementXemplate(elName);
		if (!x.attributes) x.attributes = {};
		if (!x.attributes[atName]) x.attributes[atName] = {
			order: "after",
			shown: false,
			layout: "inline"
		};
		if (x.attributes[atName].shown == "false") x.attributes[atName].shown = false;
		return x.attributes[atName];
	};


	renderElement(elName) {
		var $details = $(".designer .details").html("");
		this.renderElementShown(elName);
		if (this.getElementXemplate(elName).shown) {
			if (this.xemaDesigner.xema.root != elName) this.renderElementLayout(elName);
			this.renderElementStyles(elName);
			this.renderElementLabel(elName);
		}
	};

	renderAttribute(elName, atName) {
		var $details = $(".designer .details").html("");
		this.renderAttributeShown(elName, atName);
		if (this.getAttributeXemplate(elName, atName).shown) {
			this.renderAttributeOrder(elName, atName);
			this.renderAttributeLayout(elName, atName);
			this.renderAttributeStyles(elName, atName);
			this.renderAttributeLabel(elName, atName);
		}
	};

	renderElementLabel(elName) {
		var x = this.getElementXemplate(elName);
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title'>Label</div>");
		$block.append("<input class='textbox' value='" + (x.label ? x.label.replace("'", "&apos;").replace(">", "&gt;").replace("<", "&lt;") : "") + "'/>");
		$block.find("input").on("change", function(event) {
			this.changeElementLabel(elName, $(event.target).val());
		}.bind(this));
	};

	renderAttributeLabel(elName, atName) {
		var x = this.getAttributeXemplate(elName, atName);
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title'>Label</div>");
		$block.append("<input class='textbox' value='" + (x.label ? x.label.replace("'", "&apos;").replace(">", "&gt;").replace("<", "&lt;") : "") + "'/>");
		$block.find("input").on("change", function(event) {
			this.changeAttributeLabel(elName, atName, $(event.target).val());
		}.bind(this));
	};

	changeElementLabel(elName, label) {
		var x = this.getElementXemplate(elName);
		x.label = label;
		this.xemaDesigner.selectElement(elName);
		this.onchange();
	};

	changeAttributeLabel(elName, atName, label) {
		var x = this.getAttributeXemplate(elName, atName);
		x.label = label;
		this.xemaDesigner.selectAttribute(elName, atName);
		this.onchange();
	};

	renderElementShown(elName) {
		var x = this.getElementXemplate(elName);
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title'>Visibility</div>");
		$block.append("<label class='radio'><input type='radio' name='shown' value='true' " + (x.shown ? "checked" : "") + "/>Shown</label>");
		$block.append("<label class='radio'><input type='radio' name='shown' value='false' " + (!x.shown ? "checked" : "") + "/>Hidden</label>");
		$block.find("input").on("click change", function(event) {
			this.changeElementShown(elName, $(event.target).val());
		}.bind(this));
	};

	renderAttributeShown(elName, atName) {
		var x = this.getAttributeXemplate(elName, atName);
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title'>Visibility</div>");
		$block.append("<label class='radio'><input type='radio' name='shown' value='true' " + (x.shown ? "checked" : "") + "/>Shown</label>");
		$block.append("<label class='radio'><input type='radio' name='shown' value='false' " + (!x.shown ? "checked" : "") + "/>Hidden</label>");
		$block.find("input").on("click change", function(event) {
			this.changeAttributeShown(elName, atName, $(event.target).val());
		}.bind(this));
	};

	changeElementShown(elName, shown) {
		var x = this.getElementXemplate(elName);
		x.shown = (shown == "true" ? true : false);
		this.xemaDesigner.selectElement(elName);
		this.onchange();
	};

	changeAttributeShown(elName, atName, shown) {
		var x = this.getAttributeXemplate(elName, atName);
		x.shown = (shown == "true" ? true : false);
		this.xemaDesigner.selectAttribute(elName, atName);
		this.onchange();
	};

	renderAttributeOrder(elName, atName) {
		var x = this.getAttributeXemplate(elName, atName);
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title'>Position</div>");
		$block.append("<label class='radio'><input type='radio' name='order' value='before' " + (x.order == "before" ? "checked" : "") + "/>Before element content</label>");
		$block.append("<label class='radio'><input type='radio' name='order' value='after' " + (x.order == "after" ? "checked" : "") + "/>After element content</label>");
		$block.find("input").on("click change", function(event) {
			this.changeAttributeOrder(elName, atName, $(event.target).val());
		}.bind(this));
	};

	changeAttributeOrder(elName, atName, val) {
		var x = this.getAttributeXemplate(elName, atName);
		x.order = val;
		this.xemaDesigner.selectAttribute(elName, atName);
		this.onchange();
	};

	renderElementLayout(elName) {
		var x = this.getElementXemplate(elName);
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title'>Layout</div>");
		$block.append("<label class='radio'><input type='radio' name='layout' value='block' " + (x.layout == "block" ? "checked" : "") + "/>Line break before and after</label>");
		$block.append("<label class='radio'><input type='radio' name='layout' value='inline' " + (x.layout == "inline" ? "checked" : "") + "/>Inline</label>");
		$block.find("input").on("click change", function(event) {
			this.changeElementLayout(elName, $(event.target).val());
		}.bind(this));
	};

	renderAttributeLayout(elName, atName) {
		var x = this.getAttributeXemplate(elName, atName);
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title'>Layout</div>");
		$block.append("<label class='radio'><input type='radio' name='layout' value='block' " + (x.layout == "block" ? "checked" : "") + "/>Line break before and after</label>");
		$block.append("<label class='radio'><input type='radio' name='layout' value='inline' " + (x.layout == "inline" ? "checked" : "") + "/>Inline</label>");
		$block.find("input").on("click change", function(event) {
			this.changeAttributeLayout(elName, atName, $(event.target).val());
		}.bind(this));
	};

	changeElementLayout(elName, val) {
		var x = this.getElementXemplate(elName);
		x.layout = val;
		this.xemaDesigner.selectElement(elName);
		this.onchange();
	};

	changeAttributeLayout(elName, atName, val) {
		var x = this.getAttributeXemplate(elName, atName);
		x.layout = val;
		this.xemaDesigner.selectAttribute(elName, atName);
		this.onchange();
	};

	renderElementStyles(elName) {
		var x = this.getElementXemplate(elName);
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title tight'>Appearance</div>");
		var $table = $("<table></table>").appendTo($block);
		var dims = [];
		for (var dim in Xemplatron.styles) dims.push(dim);
		dims.reverse();
		for (var iDim = 0; iDim < dims.length; iDim++) {
			var dim = dims[iDim];
			var qualifies = true;
			if ((dim == "separation" || dim == "gutter") && this.xemaDesigner.xema.root == elName) qualifies = false;
			if ((dim == "innerPunc" || dim == "weight" || dim == "slant" || dim == "colour" || dim == "textsize") && (this.xemaDesigner.xema.elements[elName].filling == "chd" || this.xemaDesigner.xema.elements[elName].filling == "med")) qualifies = false;
			if ((dim == "captioning") && this.xemaDesigner.xema.elements[elName].filling != "lst") qualifies = false;
			if (qualifies) {
				var $row = $("<tr><td class='cell1'></td><td class='cell9'></td></tr>").appendTo($table);
				$row.find("td.cell1").append("<div class='caption'>" + Xemplatron.styles[dim].title + "</div>");
				$row.find("td.cell9").append("<select name='" + dim + "' class='" + (!x[dim] ? "none" : "") + "'><option value=''>(none)</option></select>");
				for (var styleID in Xemplatron.styles[dim])
					if (styleID != "title") {
						$row.find("select").append("<option value='" + styleID + "' " + (x[dim] && x[dim] == styleID ? "selected='selected'" : "") + ">" + Xemplatron.styles[dim][styleID].title + "</option>");
						$row.find("select").on("change", function(event) {
							this.changeElementStyle(elName, $(event.target).prop("name"), $(event.target).val());
						}.bind(this));
					}
			}
		}
	};

	renderAttributeStyles(elName, atName) {
		var x = this.getAttributeXemplate(elName, atName);
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title tight'>Appearance</div>");
		var $table = $("<table></table>").appendTo($block);
		var dims = [];
		for (var dim in Xemplatron.styles) dims.push(dim);
		dims.reverse();
		for (var iDim = 0; iDim < dims.length; iDim++) {
			var dim = dims[iDim];
			var qualifies = true;
			if ((dim == "captioning") && this.xemaDesigner.xema.elements[elName].attributes[atName].filling != "lst") qualifies = false;
			if (qualifies) {
				var $row = $("<tr><td class='cell1'></td><td class='cell9'></td></tr>").appendTo($table);
				$row.find("td.cell1").append("<div class='caption'>" + Xemplatron.styles[dim].title + "</div>");
				$row.find("td.cell9").append("<select name='" + dim + "' class='" + (!x[dim] ? "none" : "") + "'><option value=''>(none)</option></select>");
				for (var styleID in Xemplatron.styles[dim])
					if (styleID != "title") {
						$row.find("select").append("<option value='" + styleID + "' " + (x[dim] && x[dim] == styleID ? "selected='selected'" : "") + ">" + Xemplatron.styles[dim][styleID].title + "</option>");
						$row.find("select").on("change", function(event) {
							this.changeAttributeStyle(elName, atName, $(event.target).prop("name"), $(event.target).val());
						}.bind(this));
					}
			}
		}
	};

	changeElementStyle(elName, dim, val) {
		var x = this.getElementXemplate(elName);
		x[dim] = val;
		this.xemaDesigner.selectElement(elName);
		this.onchange();
	};

	changeAttributeStyle(elName, atName, dim, val) {
		var x = this.getAttributeXemplate(elName, atName);
		x[dim] = val;
		this.xemaDesigner.selectAttribute(elName, atName);
		this.onchange();
	};

}


window.XemplateDesignerClass = XemplateDesignerClass
