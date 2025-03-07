class NVHFormattingEditorClass {
  constructor() {
    this.formattingEditorComponent = null,
    this.schema = null,
    this.schemaHistory = null,
    this.schemaHistoryIndex = null,
    this.elementsSchema = null,
    this.global = null,
    observable(this);
  }

  resetSchema() {
    window.nvhFormattingEditor.schema = {
      orientation: "column",
      children: [
        {
          status: {
            isActive: false,
            isDragged: false,
          },
          orientation: "column",
          type: "placeholder",
          content: {
            name: "entry",
            fullName: "entry",
            area: "entry",
            areaFullName: "entry",
            color: window.nvhStore.getElementColor("entry"),
            canHaveChildren: true,
          },
          children: [],
        }
      ]
    },
    window.nvhFormattingEditor.global.selectedPlaceholderAreaFullName = "";
    window.nvhFormattingEditor.formattingEditorComponent.update();
  }

  clearStatuses(state) {
    if (state === null) {
      return;
    }
    Array.from(state.children).map(child => this.clearStatuses(child));
    state.children.map(child => {
      child.status.isActive = false;
      child.status.isHovered = false;
      child.status.isDragged = false;
    });
  }

  undoSchema() {
    if (window.nvhFormattingEditor.schemaHistoryIndex > 0) {
      window.nvhFormattingEditor.schemaHistoryIndex -= 1;
      window.nvhFormattingEditor.schema = JSON.parse(JSON.stringify(window.nvhFormattingEditor.schemaHistory.at(window.nvhFormattingEditor.schemaHistoryIndex)));
      window.nvhFormattingEditor.clearStatuses(window.nvhFormattingEditor.schema);
      window.nvhFormattingEditor.global.selectedPlaceholderAreaFullName = "";
      window.nvhFormattingEditor.formattingEditorComponent.update();
    }
  }

  redoSchema() {
    if (window.nvhFormattingEditor.schemaHistoryIndex < window.nvhFormattingEditor.schemaHistory.length - 1) {
      window.nvhFormattingEditor.schemaHistoryIndex += 1;
      window.nvhFormattingEditor.schema = JSON.parse(JSON.stringify(window.nvhFormattingEditor.schemaHistory.at(window.nvhFormattingEditor.schemaHistoryIndex)));
      window.nvhFormattingEditor.clearStatuses(window.nvhFormattingEditor.schema);
      window.nvhFormattingEditor.global.selectedPlaceholderAreaFullName = "";
      window.nvhFormattingEditor.formattingEditorComponent.update();
    }
  }

  createElementsSchema() {
    return window.nvhFormattingEditor.createElementsSchemaRec(window.store.schema.getRoot());
  }

  createElementsSchemaRec(element) {
    let objectStructure = {
      data: {
        type: "choice-item",
        name: element.name,
        fullName: element.path,
        color: window.nvhStore.getElementColor(element.path),
        children: [],
      },
    };
    for (let child of element.children) {
      let newElement = this.createElementsSchemaRec(child);
      objectStructure.data.children.push(newElement)
    }
    return objectStructure;
  }

  clearIsHoveredStatus() {
    window.nvhFormattingEditor.clearIsHoveredStatusRec(window.nvhFormattingEditor.schema);
  }

  clearIsHoveredStatusRec(state) {
    if (state === null) {
      return null;
    }
    Array.from(state.children).map(child => this.clearIsHoveredStatusRec(child));
    state.children.map(child => child.status.isHovered = false);
  }

  // RENAME ?
  closeActionPanel() {
    this.closeActionPanelRec(window.nvhFormattingEditor.schema);
  }

  // RENAME ?
  closeActionPanelRec(state) {
    if (state === null) {
      return null;
    }
    Array.from(state.children).map(child => this.closeActionPanelRec(child));
    state.children.map(child => child.status.isActive = false);
  }

  // RENAME ?
  openActionPanel(child) {
    if (window.nvhFormattingEditor.global.canOpenActionPanel) {
      let currentIsActive = child.status.isActive
      window.nvhFormattingEditor.closeActionPanel(); /*close actionPanel if any was opened*/
      child.status.isActive = !currentIsActive; /*clicking on selected placeholder should unselect it*/
      if (child.status.isActive && child.content.name === "") { /*setting of valid choice elements (only empty placeholders)*/
        window.nvhFormattingEditor.global.selectedPlaceholderAreaFullName = child.content.areaFullName;            
      } else {
        window.nvhFormattingEditor.global.selectedPlaceholderAreaFullName = "";
      }
    } else {
      child.status.isActive = false;
    }
    window.nvhFormattingEditor.global.canOpenActionPanel = false;
  }

  isChildOfParent(child, parent) {
    if (window.nvhFormattingEditor.global.draggedPlaceholder != null) {
      return window.nvhFormattingEditor.isChildObjectOfParent(window.nvhFormattingEditor.global.draggedPlaceholder, parent);
    }
    let result = child.includes(parent);
    let alternative = window.nvhFormattingEditor.global.draggedElementFullName === "";
    return result || alternative;
  }

  isChildObjectOfParent(childObject, parent) {
    if (childObject.content.fullName === parent && childObject.children.length !== 0) {
      /*This avoids placing a wrapper with label "parent" into another wrapper with label "parent"*/
      return false;
    }
    let result = childObject.content.fullName.includes(parent);
    let alternative = childObject.content.fullName === "";
    if (!result && !alternative) {
      return false;
    }

    for (let child of childObject.children) {
      if (!this.isChildObjectOfParent(child, parent)) {
        return false;
      }
    }
    return true;
  }

  /*TODO: it seems like label is here always null, figure out why*/
  addElement(index, component, state, editingMode, label) {
    let newElement = {
      status: {
        isActive: true,
        isHovered: true,
        isDragged: false,
      },
      orientation: editingMode,
      type: "placeholder",
      content: {
        name: label == null ? "" : label.name,
        fullName: label == null ? "" : label.fullName,
        area: label == null ? "" : label.area,
        areaFullName: label == null ? "" : label.areaFullName,
        color: label == null ? "": label.color,
        canHaveChildren: true, /*NOTE: really always true ?*/
      },
      children: []
    };
    window.nvhFormattingEditor.closeActionPanel();
    window.nvhFormattingEditor.clearIsHoveredStatus();
    window.nvhFormattingEditor.global.selectedPlaceholderAreaFullName = state.content.areaFullName;
    state.children.splice(index, 0, newElement);
    window.nvhFormattingEditor.formattingEditorComponent.update();
    window.nvhFormattingEditor.global.canOpenActionPanel = false;
  }

  addElementWithChildren(index, component, state, element, label) {
    /*label can not be null or undefined*/
    if (label == null || label == undefined) {
      return;
    }
    let newElement = {
      status: {
        isActive: false,
        isHovered: false,
        isDragged: false,
      },
      orientation: "column",
      type: "placeholder",
      content: {
        name: label.name,
        fullName: label.fullName,
        area: label.name,
        areaFullName: label.fullName,
        color: label.color,
        canHaveChildren: label.canHaveChildren !== undefined ? label.canHaveChildren : label.children.length !== 0,
      },
      children: []
    };

    if (state != null) {
      state.children.splice(index, 0, newElement);
    }
    if (label.children !== undefined && label.children !== null && element.content.areaFullName != label.areaFullName) {
      /*
      Children are present.
      When I drop to an plus icon e.g. pronunciation and the parent
      is also of type pronunciation, so that it will not render all the children.
      */
      /*
      If element has children, append also this element,
      so that it is displayed together with its children.
      */
      if (label.children.length !== 0) {
        let selfDisplayElement = {
          status: {
            isActive: false,
            isHovered: false,
            isDragged: false,
          },
          orientation: "column",
          type: "placeholder",
          content: {
            name: label.name,
            fullName: label.fullName,
            area: label.name,
            areaFullName: label.fullName,
            color: label.color,
            canHaveChildren: false,
          },
          children: []
        };
        newElement.children.push(selfDisplayElement);
      }
      for(let child of label.children) {
        let childElement = this.addElementWithChildren(null, null, null, newElement, child.data);
        newElement.children.push(childElement);
      }
    }
    if (component != null) {
      window.nvhFormattingEditor.formattingEditorComponent.update();
    }
    return newElement;
  }

  deleteElement(indexToDelete, parentState) {
    parentState.children = Array.from(parentState.children).filter((child, index) => index != indexToDelete);
    window.nvhFormattingEditor.global.canOpenActionPanel = false;
    window.nvhFormattingEditor.global.draggedElementFullName = "";
    window.nvhFormattingEditor.formattingEditorComponent.update(); // NOTE: here was updated only edit-layout, but maybe does not matter
  }

  childWithInheritedArea(child, state) {
    if (state === null) {
      return child;
    }
    child.content.area = child.content.name === "" ? state.content.area : child.content.name;
    child.content.areaFullName = child.content.name === "" ? state.content.areaFullName : child.content.fullName;
    return child;
  }

  canHaveAdders(parentFullName, placeholder) {
    if (parentFullName === placeholder.content.fullName) {
      return false;
    }
    if (!placeholder.content.canHaveChildren) {
      return false;
    }
    return true;
  }
}

window.nvhFormattingEditor = new NVHFormattingEditorClass();