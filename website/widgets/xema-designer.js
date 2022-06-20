class XemaDesignerClass {
	constructor() {
		this.xema = null
	}

	onchange() {}

	isValidXmlName(str) {
		if (str == "") return false;
		if (/[=\s\"\']/.test(str)) return false;
		try {
			$.parseXML("<" + str + "/>");
		} catch (err) {
			return false;
		}
		return true;
	}
	isEmptyObject(obj) {
		for (var prop in obj)
			if (Object.prototype.hasOwnProperty.call(obj, prop)) return false;
		return true;
	}
	start(xema) { //the editor can be an HTML element, or the string ID of one.
		this.xema = xema;
		if (typeof(editor) == "string") editor = document.getElementById(editor);
		var $editor = $("#editor").addClass("designer");
		$editor.append("<div class='list'></div><div class='details'></div>");
		this.listNodes();
		this.selectElement(xema.root);
	}
	getParentlessElements() {
		var ret = [];
		var childNames = [];
		for (var elName in this.xema.elements) {
			if (this.canHaveChildren(elName)) {
				this.xema.elements[elName].children.forEach(function(child) {
					childNames.push(child.name);
				}, this);
			}
		}
		for (var elName in this.xema.elements) {
			if (elName != this.xema.root && childNames.indexOf(elName) == -1) ret.push(elName);
		}
		return ret;
	}


	hasAttributes(elName) {
		return this.xema.elements[elName].attributes && !this.isEmptyObject(this.xema.elements[elName].attributes);
	};

	hasChildren(elName) {
		if ((this.xema.elements[elName].filling == "chd" || this.xema.elements[elName].filling == "inl") && !this.xema.elements[elName].children) this.xema.elements[elName].children = [];
		return (this.xema.elements[elName].filling == "chd" || this.xema.elements[elName].filling == "inl") && this.xema.elements[elName].children.length > 0;
	};

	canHaveChildren(elName) {
		if ((this.xema.elements[elName].filling == "chd" || this.xema.elements[elName].filling == "inl") && !this.xema.elements[elName].children) this.xema.elements[elName].children = [];
		return (this.xema.elements[elName].filling == "chd" || this.xema.elements[elName].filling == "inl")
	};

	canElementHaveValues(elName) {
		return (this.xema.elements[elName].filling == "lst")
	};

	canAttributeHaveValues(elName, atName) {
		return (this.xema.elements[elName].attributes[atName].filling == "lst")
	};


	listNodes() {
		var $list = $(".designer .list");
		var scrollTop = $list.scrollTop();
		$list.html("");
		this.listElement(this.xema.root, $list, 0);
		this.resizeBlinders();
		var parentless = this.getParentlessElements();
		if (parentless.length > 0) {
			$("<div class='title'><span>Unattached elements</span></div>").appendTo($list);
			parentless.forEach(function(elName) {
				this.listElement(elName, $list, 0);
			}, this);
		}
		$list.scrollTop(scrollTop);
	}

	listElement(elName, $list, level) {
		var elNamesDone = [];
		var isSuspect = (this.xema._dtd ? true : false); //all xemas that originate from a DTD are inherently suspect
		if (this.xema.elements[elName] && (!isSuspect || elNamesDone.indexOf(elName) == -1)) {
			elNamesDone.push(elName);
			var hasEponymousAscendant = ($list.closest(".container." + elName.replace(/\./g, "\\.")).length > 0);
			var collapsed = "";
			if ((this.hasAttributes(elName) || this.hasChildren(elName)) && !hasEponymousAscendant) collapsed += " hasChildren";
			var parName = $list.closest(".container").find(".element").first().data("elName");
			if (this.xema.elements[elName]._collapsedUnder && this.xema.elements[elName]._collapsedUnder[parName]) collapsed += " collapsed";
			if (level > 5) collapsed += " collapsed";
			var $c = $("<div class='container " + elName + " " + collapsed + "'></div>").appendTo($list);
			$("<div class='horizontal'><span class='plusminus'></span></div>").appendTo($c).on("click", function(event) {
				this.plusminus($(event.delegateTarget.parentNode))
			}.bind(this));
			var html = "<span class='tech'><span class='brak'>&lt;</span><span class='elm'>" + elName + "</span><span class='brak'>&gt;</span></span>";
			$("<div class='clickable element " + (this.xema.root == elName ? "root" : "") + "'>" + html + "</div>").appendTo($c).data("elName", elName).on("click", function(event) {
				this.selectElement($(event.delegateTarget).data("elName"))
			}.bind(this));
			if ((this.hasAttributes(elName) || this.hasChildren(elName)) && !hasEponymousAscendant) {
				var $sublist = $("<div class='children'></div>").appendTo($c);
				if (this.hasAttributes(elName)) {
					for (var atName in this.xema.elements[elName].attributes) {
						var $c = $("<div class='container'></div>").appendTo($sublist);
						$("<div class='horizontal'></div>").appendTo($c);
						var html = "<span class='tech'><span class='ats'>@</span><span class='att'>" + atName + "</span></span>";
						$("<div class='clickable attribute'>" + html + "</div>").appendTo($c).data("elName", elName).data("atName", atName).on("click", function(event) {
							this.selectAttribute($(event.delegateTarget).data("elName"), $(event.delegateTarget).data("atName"))
						}.bind(this));;
					}
				}
				if (this.hasChildren(elName)) {
					if (true) {
						this.xema.elements[elName].children.forEach(function(item) {
							var childName = item.name;
							this.listElement(childName, $sublist, level + 1);
						}, this);
					}
				}
				var $blinder = $("<div class='blinder'></div>").appendTo($sublist);
				this.resizeBlinders($blinder);
			}
		}
	};

	plusminus($divContainer) {
		var elName = $divContainer.find(".element").first().data("elName");
		var parName = $divContainer.parent().closest(".container").find(".element").first().data("elName");
		var el = this.xema.elements[elName];
		if ($divContainer.hasClass("collapsed")) {
			$divContainer.removeClass("collapsed");
			if (el._collapsedUnder) delete el._collapsedUnder[parName];
		} else {
			$divContainer.addClass("collapsed");
			if (!el._collapsedUnder) el._collapsedUnder = {};
			el._collapsedUnder[parName] = true;
		}
		this.resizeBlinders();
	}

	resizeBlinders($blinder) {
		if ($blinder) {
			go($blinder)
		} else {
			$(".designer .blinder").each(function() {
				var $blinder = $(this);
				go($blinder)
			});
		}

		function go($blinder) {
			var $prev = $blinder.prev();
			if ($prev.length > 0) {
				$blinder.css({
					top: $prev.position().top + 16
				});
			}
		}
	};


	selectElement(elName) {
		$(".designer .list *").removeClass("current");
		$(".designer .list .element").each(function() {
			if ($(this).data("elName") == elName) $(this).addClass("current")
		});
		this.renderElement(elName);
	};

	selectAttribute(elName, atName) {
		$(".designer .list *").removeClass("current");
		$(".designer .list .attribute").each(function() {
			if ($(this).data("elName") == elName && $(this).data("atName") == atName) $(this).addClass("current")
		});
		this.renderAttribute(elName, atName);
	};


	renderElement(elName) {
		var $details = $(".designer .details").html("");
		this.renderElementName(elName);
		this.renderElementAttributes(elName);
		this.renderElementFilling(elName);
		if (this.canHaveChildren(elName)) this.renderElementChildren(elName);
		if (this.canElementHaveValues(elName)) this.renderElementValues(elName);
		//$details.hide().fadeIn("fast");
	};

	renderAttribute(elName, atName) {
		var $details = $(".designer .details").html("");
		this.renderAttributeName(elName, atName);
		this.renderAttributeFilling(elName, atName);
		if (this.canAttributeHaveValues(elName, atName)) this.renderAttributeValues(elName, atName);
		//$details.hide().fadeIn("fast");
	};


	deleteElement(elName) {
		delete this.xema.elements[elName];
		this.deleteChildRefs(elName);
		this.listNodes();
		$(".designer .details").html("");
		this.onchange();
	};

	deleteAttribute(elName, atName) {
		delete this.xema.elements[elName].attributes[atName];
		this.listNodes();
		this.selectElement(elName);
		this.onchange();
	};

	deleteChildRefs(elName) {
		for (var parName in this.xema.elements) {
			var par = this.xema.elements[parName];
			if (par.filling == "chd" || par.filling == "inl") {
				var children = [];
				par.children.forEach(function(item) {
					if (item.name != elName) children.push(item);
				});
				par.children = children;
			}
		}
		this.onchange();
	};


	setRoot(elName) {
		$(".designer .details").html("");
		this.xema.root = elName;
		this.listNodes();
		this.selectElement(elName);
		this.onchange();
	};


	renderElementName(elName) {
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title'>Element</div>");
		$("<input class='textbox tech elName'/>").appendTo($block).val(elName).on("keyup change", function(event) {
			$(".designer .errInvalidRename").hide();
			$(".designer .errRenameExists").hide();
			if (event.type == "keyup" && event.which == 13) this.renameElement(elName, $(".designer input.elName").val()); //enter
			else {
				if (event.type == "keyup" && event.which == 27) $(".designer input.elName").val(elName); //escape
				if ($(event.target).val() != elName) {
					$(".designer .butRename").show();
					$(".designer .butRenameCancel").show();
					$(".designer .butDeleteElement").hide();
				} else {
					$(".designer .butRename").hide();
					$(".designer .butRenameCancel").hide();
					$(".designer .butDeleteElement").show();
					$(".designer .errInvalidRename").hide();
					$(".designer .errRenameExists").hide();
				}
			}
		}.bind(this));
		$("<button class='butRename iconAccept'>Rename</button>").hide().appendTo($block).on("click", function(event) {
			this.renameElement(elName, $(".designer input.elName").val())
		}.bind(this));
		$("<button class='butRenameCancel iconCancel'>Cancel renaming</button>").hide().appendTo($block).on("click", function(event) {
			$(".designer input.elName").val(elName);
			$(".designer .butRename").hide();
			$(".designer .butRenameCancel").hide();
			$(".designer .butDeleteElement").show();
		}.bind(this));
		if (this.xema.root != elName) $("<button class='butDeleteElement iconCross'>Delete element</button>").appendTo($block).on("click", function(event) {
			this.deleteElement(elName)
		}.bind(this));
		$("<div class='warn errInvalidRename'>Cannot rename, not a valid XML name.</div>").appendTo($block).hide();
		$("<div class='warn errRenameExists'>Cannot rename, such element already exists.</div>").appendTo($block).hide();
	};

	renderAttributeName(elName, atName) {
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title'>Attribute</div>");
		$("<input class='textbox tech atName'/>").appendTo($block).val(atName).on("keyup change", function(event) {
			$(".designer .errInvalidAtName").hide();
			$(".designer .errAtNameExists").hide();
			if (event.type == "keyup" && event.which == 13) this.renameAttribute(elName, atName, $(".designer input.atName").val()); //enter
			else {
				if (event.type == "keyup" && event.which == 27) $(".designer input.atName").val(atName); //escape
				if ($(event.target).val() != atName) $(".designer .butRename").show();
				else $(".designer .butRename").hide();
			}
		}.bind(this));
		$("<button class='butRename iconAccept'>Rename</button>").hide().appendTo($block).on("click", function(event) {
			this.renameAttribute(elName, atName, $(".designer input.atName").val())
		}.bind(this));
		$("<button class='butDeleteAttribute iconCross'>Delete attribute</button>").appendTo($block).on("click", function(event) {
			this.deleteAttribute(elName, atName)
		}.bind(this));
		$("<div class='warn errInvalidAtName'>Cannot rename, not a valid XML name.</div>").appendTo($block).hide();
		$("<div class='warn errAtNameExists'>Cannot rename, such attribute already exists.</div>").appendTo($block).hide();
	};


	renameElement(elName, newName) {
		if (!this.isValidXmlName(newName)) {
			$(".designer .errInvalidRename").show();
		} else if (this.xema.elements[newName]) {
			$(".designer .errRenameExists").show();
		} else {
			this.xema.elements[newName] = this.xema.elements[elName];
			delete this.xema.elements[elName];
			if (this.xema.root == elName) this.xema.root = newName;
			var pars = this.renameChildRefs(elName, newName);
			this.listNodes();
			this.selectElement(newName);
			this.onchange();
		}
	};

	renameAttribute(elName, atName, newName) {
		if (!this.isValidXmlName(newName)) {
			$(".designer .errInvalidAtName").show();
		} else if (this.xema.elements[elName].attributes[newName]) {
			$(".designer .errAtNameExists").show();
		} else {
			this.xema.elements[elName].attributes[newName] = this.xema.elements[elName].attributes[atName];
			delete this.xema.elements[elName].attributes[atName];
			this.listNodes();
			this.selectAttribute(elName, newName);
			this.onchange();
		}
	};

	renameChildRefs(elName, newName) {
		for (var parName in this.xema.elements) {
			var par = this.xema.elements[parName];
			if (par.filling == "chd" || par.filling == "inl") {
				par.children.forEach(function(item) {
					if (item.name == elName) item.name = newName;
				});
			}
		}
		this.onchange();
	};


	renderElementAttributes(elName) {
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title tight'>Attributes</div>");
		if (this.hasAttributes(elName)) {
			var $table = $("<table></table>").appendTo($block);
			for (var atName in this.xema.elements[elName].attributes) {
				var at = this.xema.elements[elName].attributes[atName];
				var $row = $("<tr><td class='cell1'></td><td class='cell2'></td><td class='cell9'></td></tr>").appendTo($table);

				var html = "<span class='tech'><span class='ats'>@</span><span class='att'>" + atName + "</span></span>";
				$(html).appendTo($row.find("td.cell1")).data("atName", atName).on("click", function(event) {
					this.selectAttribute(elName, $(event.delegateTarget).data("atName"));
				}.bind(this));

				var $settings = $("<span><label class='radio'><input type='radio' name='" + atName + "' value='optional' " + (at.optionality == "optional" ? "checked" : "") + "/>optional</label> <label class='radio'><input type='radio' name='" + atName + "' value='obligatory' " + (at.optionality == "obligatory" ? "checked" : "") + "/>obligatory</label></span>").appendTo($row.find("td.cell2"));
				$settings.find("input").data("atName", atName).on("click change", function(event) {
					this.changeOptionality(elName, $(event.target).data("atName"), $(event.target).val());
				}.bind(this));

				$("<button class='iconOnly iconArrowUp'>&nbsp;</button>").data("atName", atName).appendTo($row.find("td.cell9")).on("click", function(event) {
					this.moveAttributeUp(elName, $(event.delegateTarget).data("atName"))
				}.bind(this));
				$("<button class='iconOnly iconArrowDown'>&nbsp;</button>").data("atName", atName).appendTo($row.find("td.cell9")).on("click", function(event) {
					this.moveAttributeDown(elName, $(event.delegateTarget).data("atName"))
				}.bind(this));
				$("<button class='iconOnly iconCross'>&nbsp;</button>").data("atName", atName).appendTo($row.find("td.cell9")).on("click", function(event) {
					this.deleteAttribute(elName, $(event.delegateTarget).data("atName"))
				}.bind(this));
			}
		}
		$("<button class='butAtNewOpener iconAdd'>Add...</button>").appendTo($block).on("click", function(event) {
			$(".designer .butAtNewOpener").hide();
			$(".designer .txtAtNew").show().focus();
			$(".designer .butAtNew").show();
			$(".designer .butAtNewCancel").show();
		});
		$("<input class='textbox tech atName txtAtNew'/>").hide().appendTo($block).on("keyup change", function(event) {
			$(".designer .errInvalidAtName").hide();
			$(".designer .errAtNameExists").hide();
			if (event.type == "keyup" && event.which == 13) this.addAttribute(elName, $(".designer input.txtAtNew").val());
			else if (event.type == "keyup" && event.which == 27) {
				$(".designer input.txtAtNew").val("");
				$(".designer .txtAtNew").hide().focus();
				$(".designer .butAtNew").hide();
				$(".designer .butAtNewCancel").hide();
				$(".designer .butAtNewOpener").show();
			}
		}.bind(this));
		$("<button class='butAtNew iconAccept'>Add</button>").hide().appendTo($block).on("click", function(event) {
			this.addAttribute(elName, $(".designer input.atName").val())
		}.bind(this));
		$("<button class='butAtNewCancel iconCancel'>Cancel</button>").hide().appendTo($block).on("click", function(event) {
			$(".designer .errInvalidAtName").hide();
			$(".designer .errAtNameExists").hide();
			$(".designer input.txtAtNew").val("");
			$(".designer .txtAtNew").hide().focus();
			$(".designer .butAtNew").hide();
			$(".designer .butAtNewCancel").hide();
			$(".designer .butAtNewOpener").show();
		});
		$("<div class='warn errInvalidAtName'>Cannot add, not a valid XML name.</div>").appendTo($block).hide();
		$("<div class='warn errAtNameExists'>Cannot add, such attribute already exists.</div>").appendTo($block).hide();
	}

	renderElementChildren(elName) {
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title tight'>Child elements</div>");
		if (this.hasChildren(elName)) {
			var $table = $("<table></table>").appendTo($block);
			this.xema.elements[elName].children.forEach(function(child) {
				var $row = $("<tr><td class='cell1'></td><td class='cell2'></td><td class='cell9'></td></tr>").appendTo($table);

				var html = "<span class='tech'><span class='brak'>&lt;</span><span class='elm'>" + child.name + "</span><span class='brak'>&gt;</span></span>";
				$(html).appendTo($row.find("td.cell1")).data("elName", child.name).on("click", function(event) {
					this.selectElement($(event.delegateTarget).data("elName"));
				}.bind(this));
				child.min = parseInt(child.min);
				child.max = parseInt(child.max);
				var $settings = $("<span>min <input class='textbox min' value='" + (child.min ? child.min : "") + "'/> max <input class='textbox max' value='" + (child.max ? child.max : "") + "'/><button class='change iconAccept'>Change</button><button class='cancel iconCancel'>Cancel</button></span>").appendTo($row.find("td.cell2"));
				$settings.find("input.min").data("orig", (child.min ? child.min : "")).data("childName", child.name);
				$settings.find("input.max").data("orig", (child.max ? child.max : "")).data("childName", child.name);
				$settings.find("button").data("childName", child.name).hide();
				$settings.find("input").on("keyup change", function(event) {
					if (event.type == "keyup" && event.which == 27) {
						$settings.find("button").hide();
						$settings.find("input.min").val($settings.find("input.min").data("orig"));
						$settings.find("input.max").val($settings.find("input.max").data("orig"));
					} else if (event.type == "keyup" && event.which == 13) {
						this.changeMinMax(elName, child.name, $settings.find("input.min").val(), $settings.find("input.max").val());
					} else {
						$settings.find("button").show();
					}
				}.bind(this));
				$settings.find("button.change").on("click", function(event) {
					this.changeMinMax(elName, child.name, $settings.find("input.min").val(), $settings.find("input.max").val());
				}.bind(this));
				$settings.find("button.cancel").on("click", function(event) {
					$settings.find("button").hide();
					$settings.find("input.min").val($settings.find("input.min").data("orig"));
					$settings.find("input.max").val($settings.find("input.max").data("orig"));
				});

				$("<button class='iconOnly iconArrowUp'>&nbsp;</button>").data("elName", child.name).appendTo($row.find("td.cell9")).on("click", function(event) {
					this.moveElementUp(elName, $(event.delegateTarget).data("elName"))
				}.bind(this));
				$("<button class='iconOnly iconArrowDown'>&nbsp;</button>").data("elName", child.name).appendTo($row.find("td.cell9")).on("click", function(event) {
					this.moveElementDown(elName, $(event.delegateTarget).data("elName"))
				}.bind(this));
				$("<button class='iconOnly iconCross'>&nbsp;</button>").appendTo($row.find("td.cell9")).data("elName", child.name).on("click", function(event) {
					this.detachElement(elName, $(event.delegateTarget).data("elName"))
				}.bind(this));
			}, this);
		}
		$("<button class='butElNewOpener iconAdd'>Add...</button>").appendTo($block).on("click", function(event) {
			$(".designer .butElNewOpener").hide();
			$(".designer .txtElNew").show().focus();
			$(".designer .butElNew").show();
			$(".designer .butElNewCancel").show();
		}.bind(this));
		$("<input class='textbox tech elName txtElNew'/>").hide().appendTo($block).on("keyup change", function(event) {
			$(".designer .errInvalidElName").hide();
			if (event.type == "keyup" && event.which == 13) this.addElement(elName, $(".designer input.txtElNew").val());
			else if (event.type == "keyup" && event.which == 27) {
				$(".designer input.txtElNew").val("");
				$(".designer .txtElNew").hide().focus();
				$(".designer .butElNew").hide();
				$(".designer .butElNewCancel").hide();
				$(".designer .butElNewOpener").show();
			}
		}.bind(this));
		$("<button class='butElNew iconAccept'>Add</button>").hide().appendTo($block).on("click", function(event) {
			this.addElement(elName, $(".designer input.txtElNew").val())
		}.bind(this));
		$("<button class='butElNewCancel iconCancel'>Cancel</button>").hide().appendTo($block).on("click", function(event) {
			$(".designer .errInvalidElName").hide();
			$(".designer input.txtElNew").val("");
			$(".designer .txtElNew").hide().focus();
			$(".designer .butElNew").hide();
			$(".designer .butElNewCancel").hide();
			$(".designer .butElNewOpener").show();
		});
		$("<div class='warn errInvalidElName'>Cannot add, not a valid XML name.</div>").appendTo($block).hide();
	}


	addAttribute(elName, atName) {
		if (!this.xema.elements[elName].attributes) this.xema.elements[elName].attributes = {};
		if (!this.isValidXmlName(atName)) {
			$(".designer .errInvalidAtName").show();
		} else if (this.xema.elements[elName].attributes[atName]) {
			$(".designer .errAtNameExists").show();
		} else {
			this.xema.elements[elName].attributes[atName] = {
				optionality: "optional",
				filling: "txt"
			};
			this.listNodes();
			this.selectElement(elName);
			this.onchange();
		}
	};

	addElement(parName, elName) {
		if (!this.isValidXmlName(elName)) {
			$(".designer .errInvalidElName").show();
		} else {
			if (!this.xema.elements[elName]) this.xema.elements[elName] = {
				filling: "chd",
				children: [],
				attributes: {}
			};
			this.xema.elements[parName].children.push({
				name: elName,
				min: 0,
				max: 0,
				rec: 0
			});
			this.listNodes();
			this.selectElement(parName);
			this.onchange();
		}
	};

	detachElement(parName, elName) {
		var par = this.xema.elements[parName];
		var children = [];
		par.children.forEach(function(item) {
			if (item.name != elName) children.push(item);
		});
		par.children = children;
		this.listNodes();
		this.selectElement(parName);
		this.onchange();
	};

	changeMinMax(parName, childName, min, max) {
		this.xema.elements[parName].children.forEach(function(child) {
			if (child.name == childName) {
				if ($.trim(min) == "") min = 0;
				else if ($.isNumeric(min)) min = Math.abs(Math.floor(min));
				else min = child.min;
				if ($.trim(max) == "") max = 0;
				else if ($.isNumeric(max)) max = Math.abs(Math.floor(max));
				else max = child.max;
				if (max > 0 && max < min) max = min;
				child.min = min;
				child.max = max;
			}
		});
		this.selectElement(parName);
		this.onchange();
	};

	changeOptionality(elName, atName, optionality) {
		this.xema.elements[elName].attributes[atName].optionality = optionality;
		this.selectElement(elName);
		this.onchange();
	};


	renderElementFilling(elName) {
		var el = this.xema.elements[elName];
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title'>Content</div>");
		$block.append("<label class='radio'><input type='radio' name='filling' value='chd' " + (el.filling == "chd" ? "checked" : "") + "/>Child elements</label>");
		$block.append("<label class='radio'><input type='radio' name='filling' value='txt' " + (el.filling == "txt" ? "checked" : "") + "/>Text</label>");
		$block.append("<label class='radio'><input type='radio' name='filling' value='inl' " + (el.filling == "inl" ? "checked" : "") + "/>Text with markup</label>");
		$block.append("<label class='radio'><input type='radio' name='filling' value='lst' " + (el.filling == "lst" ? "checked" : "") + "/>Value from list</label>");
		$block.append("<label class='radio'><input type='radio' name='filling' value='emp' " + (el.filling == "emp" ? "checked" : "") + "/>Empty</label>");
		$block.append("<label class='radio'><input type='radio' name='filling' value='med' " + (el.filling == "med" ? "checked" : "") + "/>Media</label>");
		$block.find("input").on("click change", function(event) {
			this.changeElementFilling(elName, $(event.target).val());
		}.bind(this));
	};

	renderAttributeFilling(elName, atName) {
		var at = this.xema.elements[elName].attributes[atName];
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title'>Content</div>");
		$block.append("<label class='radio'><input type='radio' name='filling' value='txt' " + (at.filling == "txt" ? "checked" : "") + "/>Text</label>");
		$block.append("<label class='radio'><input type='radio' name='filling' value='lst' " + (at.filling == "lst" ? "checked" : "") + "/>Value from list</label>");
		$block.find("input").on("click change", function(event) {
			this.changeAttributeFilling(elName, atName, $(event.target).val());
		}.bind(this));
	};

	changeElementFilling(elName, filling) {
		var el = this.xema.elements[elName];
		el.filling = filling;
		if (filling == "chd" || filling == "inl") {
			if (!el.children) el.children = [];
			//delete el.values;
		} else if (filling == "lst") {
			//delete el.children;
			if (!el.values) el.values = [];
		} else {
			//delete el.children;
			//delete el.values;
		}
		this.listNodes();
		this.selectElement(elName);
		this.onchange();
	};

	changeAttributeFilling(elName, atName, filling) {
		var at = this.xema.elements[elName].attributes[atName];
		at.filling = filling;
		if (filling == "lst") {
			if (!at.values) at.values = [];
		} else {
			//delete at.values;
		}
		this.selectAttribute(elName, atName);
		this.onchange();
	};


	renderElementValues(elName) {
		var el = this.xema.elements[elName];
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title tight'>Values</div>");
		if (el.values.length > 0) {
			var $table = $("<table></table>").appendTo($block);
			el.values.forEach(function(obj) {
				var $row = $("<tr><td class='cell1'></td><td class='cell9'></td></tr>").appendTo($table);
				$row.find("td.cell1").append("<input class='textbox val'/><input class='textbox cap'/>");
				$row.find("td.cell1").append("<button class='change iconAccept'>Change</button><button class='cancel iconCancel'>Cancel</button>");
				$row.find("input.val").data("orig", obj.value).val(obj.value);
				$row.find("input.cap").data("orig", obj.caption).val(obj.caption);
				$row.find("button").hide();
				$row.find("input").on("keyup change", function(event) {
					$row.find("button").show();
					if (event.type == "keyup" && event.which == 27) {
						$row.find("button").hide();
						$row.find("input.val").val($row.find("input.val").data("orig"));
						$row.find("input.cap").val($row.find("input.cap").data("orig"));
					}
					if (event.type == "keyup" && event.which == 13) {
						this.changeElementValue(elName, obj.value, $row.find("input.val").val(), $row.find("input.cap").val());
					}
				}.bind(this));
				$row.find("button.change").on("click", function(event) {
					this.changeElementValue(elName, obj.value, $row.find("input.val").val(), $row.find("input.cap").val());
				}.bind(this));
				$row.find("button.cancel").on("click", function(event) {
					$row.find("button").hide();
					$row.find("input.val").val($row.find("input.val").data("orig"));
					$row.find("input.cap").val($row.find("input.cap").data("orig"));
				}.bind(this));
				$("<button class='iconOnly iconArrowUp'>&nbsp;</button>").appendTo($row.find("td.cell9")).on("click", function(event) {
					this.moveElementValueUp(elName, obj.value)
				}.bind(this));
				$("<button class='iconOnly iconArrowDown'>&nbsp;</button>").appendTo($row.find("td.cell9")).on("click", function(event) {
					this.moveElementValueDown(elName, obj.value)
				}.bind(this));
				$("<button class='iconOnly iconCross'>&nbsp;</button>").appendTo($row.find("td.cell9")).on("click", function(event) {
					this.deleteElementValue(elName, obj.value)
				}.bind(this));
			}, this);
		}
		$("<button class='butNewValue iconAdd'>Add...</button>").appendTo($block).on("click", function(event) {
			$block.find("button.butNewValue").hide();
			$block.find("input.new").show().first().focus();
			$block.find("button.butNewValueOK").show();
			$block.find("button.butNewValueCancel").show();
		});
		$("<input class='textbox new val'/>").appendTo($block);
		$("<input class='textbox new cap'/>").appendTo($block);
		$block.find("input.new").hide().on("keyup change", function(event) {
			if (event.type == "keyup" && event.which == 27) {
				$block.find("input.new").hide().val("");
				$block.find("button.butNewValueOK").hide();
				$block.find("button.butNewValueCancel").hide();
				$block.find("button.butNewValue").show();
			}
			if (event.type == "keyup" && event.which == 13) {
				this.addElementValue(elName, $block.find("input.new.val").val(), $block.find("input.new.cap").val());
			}
		}.bind(this));
		$("<button class='butNewValueOK iconAccept'>Add</button>").hide().appendTo($block).on("click", function(event) {
			this.addElementValue(elName, $block.find("input.new.val").val(), $block.find("input.new.cap").val());
		}.bind(this));
		$("<button class='butNewValueCancel iconCancel'>Cancel</button>").hide().appendTo($block).on("click", function(event) {
			$block.find("input.new").hide().val("");
			$block.find("button.butNewValueOK").hide();
			$block.find("button.butNewValueCancel").hide();
			$block.find("button.butNewValue").show();
		});
	};

	renderAttributeValues(elName, atName) {
		var at = this.xema.elements[elName].attributes[atName];
		var $block = $("<div class='block'></div>").appendTo($(".designer .details"));
		$block.append("<div class='title'>Values</div>");
		if (at.values.length > 0) {
			var $table = $("<table></table>").appendTo($block);
			at.values.forEach(function(obj) {
				var $row = $("<tr><td class='cell1'></td><td class='cell9'></td></tr>").appendTo($table);
				$row.find("td.cell1").append("<input class='textbox val'/><input class='textbox cap'/>");
				$row.find("td.cell1").append("<button class='change iconAccept'>Change</button><button class='cancel iconCancel'>Cancel</button>");
				$row.find("input.val").data("orig", obj.value).val(obj.value);
				$row.find("input.cap").data("orig", obj.caption).val(obj.caption);
				$row.find("button").hide();
				$row.find("input").on("keyup change", function(event) {
					$row.find("button").show();
					if (event.type == "keyup" && event.which == 27) {
						$row.find("button").hide();
						$row.find("input.val").val($row.find("input.val").data("orig"));
						$row.find("input.cap").val($row.find("input.cap").data("orig"));
					}
					if (event.type == "keyup" && event.which == 13) {
						this.changeAttributeValue(elName, atName, obj.value, $row.find("input.val").val(), $row.find("input.cap").val());
					}
				}.bind(this));
				$row.find("button.change").on("click", function(event) {
					this.changeAttributeValue(elName, atName, obj.value, $row.find("input.val").val(), $row.find("input.cap").val());
				}.bind(this));
				$row.find("button.cancel").on("click", function(event) {
					$row.find("button").hide();
					$row.find("input.val").val($row.find("input.val").data("orig"));
					$row.find("input.cap").val($row.find("input.cap").data("orig"));
				});
				$("<button class='iconOnly iconArrowUp'>&nbsp;</button>").appendTo($row.find("td.cell9")).on("click", function(event) {
					this.moveAttributeValueUp(elName, atName, obj.value)
				}.bind(this));
				$("<button class='iconOnly iconArrowDown'>&nbsp;</button>").appendTo($row.find("td.cell9")).on("click", function(event) {
					this.moveAttributeValueDown(elName, atName, obj.value)
				}.bind(this));
				$("<button class='iconOnly iconCross'>&nbsp;</button>").appendTo($row.find("td.cell9")).on("click", function(event) {
					this.deleteAttributeValue(elName, atName, obj.value)
				}.bind(this));
			}, this);
		}
		$("<button class='butNewValue iconAdd'>Add...</button>").appendTo($block).on("click", function(event) {
			$block.find("button.butNewValue").hide();
			$block.find("input.new").show().first().focus();
			$block.find("button.butNewValueOK").show();
			$block.find("button.butNewValueCancel").show();
		});
		$("<input class='textbox new val'/>").appendTo($block);
		$("<input class='textbox new cap'/>").appendTo($block);
		$block.find("input.new").hide().on("keyup change", function(event) {
			if (event.type == "keyup" && event.which == 27) {
				$block.find("input.new").hide().val("");
				$block.find("button.butNewValueOK").hide();
				$block.find("button.butNewValueCancel").hide();
				$block.find("button.butNewValue").show();
			}
			if (event.type == "keyup" && event.which == 13) {
				this.addAttributeValue(elName, atName, $block.find("input.new.val").val(), $block.find("input.new.cap").val());
			}
		}.bind(this));
		$("<button class='butNewValueOK iconAccept'>Add</button>").hide().appendTo($block).on("click", function(event) {
			this.addAttributeValue(elName, atName, $block.find("input.new.val").val(), $block.find("input.new.cap").val());
		}.bind(this));
		$("<button class='butNewValueCancel iconCancel'>Cancel</button>").hide().appendTo($block).on("click", function(event) {
			$block.find("input.new").hide().val("");
			$block.find("button.butNewValueOK").hide();
			$block.find("button.butNewValueCancel").hide();
			$block.find("button.butNewValue").show();
		});
	};


	deleteElementValue(elName, value) {
		var objs = [];
		this.xema.elements[elName].values.forEach(function(obj) {
			if (obj.value != value) objs.push(obj);
		});
		this.xema.elements[elName].values = objs;
		this.selectElement(elName);
		this.onchange();
	};

	deleteAttributeValue(elName, atName, value) {
		var objs = [];
		this.xema.elements[elName].attributes[atName].values.forEach(function(obj) {
			if (obj.value != value) objs.push(obj);
		});
		this.xema.elements[elName].attributes[atName].values = objs;
		this.selectAttribute(elName, atName);
		this.onchange();
	};

	changeElementValue(elName, oldValue, newValue, newCaption) {
		newValue = $.trim(newValue);
		newCaption = $.trim(newCaption);
		if (newValue != "") {
			this.xema.elements[elName].values.forEach(function(obj) {
				if (obj.value == oldValue) {
					obj.value = newValue;
					obj.caption = newCaption;
				}
			});
		}
		this.selectElement(elName);
		this.onchange();
	};

	changeAttributeValue(elName, atName, oldValue, newValue, newCaption) {
		newValue = $.trim(newValue);
		newCaption = $.trim(newCaption);
		if (newValue != "") {
			this.xema.elements[elName].attributes[atName].values.forEach(function(obj) {
				if (obj.value == oldValue) {
					obj.value = newValue;
					obj.caption = newCaption;
				}
			});
		}
		this.selectAttribute(elName, atName);
		this.onchange();
	};

	addElementValue(elName, value, caption) {
		value = $.trim(value);
		caption = $.trim(caption);
		if (value != "") this.xema.elements[elName].values.push({
			value: value,
			caption: caption
		});
		this.selectElement(elName);
		this.onchange();
	};

	addAttributeValue(elName, atName, value, caption) {
		value = $.trim(value);
		caption = $.trim(caption);
		if (value != "") this.xema.elements[elName].attributes[atName].values.push({
			value: value,
			caption: caption
		});
		this.selectAttribute(elName, atName);
		this.onchange();
	};


	moveElementUp(parName, childName) {
		var par = this.xema.elements[parName];
		var iMe = -1;
		par.children.forEach(function(obj, i) {
			if (obj.name == childName) iMe = i;
		});
		var temp = par.children[iMe - 1];
		par.children[iMe - 1] = par.children[iMe];
		par.children[iMe] = temp;
		this.listNodes();
		this.selectElement(parName);
		this.onchange();
	};

	moveElementDown(parName, childName) {
		var par = this.xema.elements[parName];
		var iMe = -1;
		par.children.forEach(function(obj, i) {
			if (obj.name == childName) iMe = i;
		});
		var temp = par.children[iMe + 1];
		par.children[iMe + 1] = par.children[iMe];
		par.children[iMe] = temp;
		this.listNodes();
		this.selectElement(parName);
		this.onchange();
	};

	moveElementValueUp(elName, value) {
		var el = this.xema.elements[elName];
		var iMe = -1;
		el.values.forEach(function(obj, i) {
			if (obj.value == value) iMe = i;
		});
		var temp = el.values[iMe - 1];
		el.values[iMe - 1] = el.values[iMe];
		el.values[iMe] = temp;
		this.selectElement(elName);
		this.onchange();
	};

	moveElementValueDown(elName, value) {
		var el = this.xema.elements[elName];
		var iMe = -1;
		el.values.forEach(function(obj, i) {
			if (obj.value == value) iMe = i;
		});
		var temp = el.values[iMe + 1];
		el.values[iMe + 1] = el.values[iMe];
		el.values[iMe] = temp;
		this.selectElement(elName);
		this.onchange();
	};

	moveAttributeValueUp(elName, atName, value) {
		var at = this.xema.elements[elName].attributes[atName];
		var iMe = -1;
		at.values.forEach(function(obj, i) {
			if (obj.value == value) iMe = i;
		});
		var temp = at.values[iMe - 1];
		at.values[iMe - 1] = at.values[iMe];
		at.values[iMe] = temp;
		this.selectAttribute(elName, atName);
		this.onchange();
	};

	moveAttributeValueDown(elName, atName, value) {
		var at = this.xema.elements[elName].attributes[atName];
		var iMe = -1;
		at.values.forEach(function(obj, i) {
			if (obj.value == value) iMe = i;
		});
		var temp = at.values[iMe + 1];
		at.values[iMe + 1] = at.values[iMe];
		at.values[iMe] = temp;
		this.selectAttribute(elName, atName);
		this.onchange();
	};

	moveAttributeUp(elName, atName) {
		var el = this.xema.elements[elName];
		var keys = [];
		for (var key in el.attributes) keys.push(key);
		var iMe = -1;
		keys.forEach(function(key, i) {
			if (key == atName) iMe = i;
		});
		var temp = keys[iMe - 1];
		keys[iMe - 1] = keys[iMe];
		keys[iMe] = temp;
		keys.forEach(function(key) {
			var obj = el.attributes[key];
			delete el.attributes[key];
			el.attributes[key] = obj;
		});
		this.listNodes();
		this.selectElement(elName);
		this.onchange();
	};

	moveAttributeDown(elName, atName) {
		var el = this.xema.elements[elName];
		var keys = [];
		for (var key in el.attributes) keys.push(key);
		var iMe = -1;
		keys.forEach(function(key, i) {
			if (key == atName) iMe = i;
		});
		var temp = keys[iMe + 1];
		keys[iMe + 1] = keys[iMe];
		keys[iMe] = temp;
		keys.forEach(function(key) {
			var obj = el.attributes[key];
			delete el.attributes[key];
			el.attributes[key] = obj;
		});
		this.listNodes();
		this.selectElement(elName);
		this.onchange();
	};
}

window.XemaDesignerClass = XemaDesignerClass
