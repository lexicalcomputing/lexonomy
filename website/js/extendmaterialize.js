let autocompleteExtension = {
   // added dropdownOptions
   _setupDropdown: function(){
      var _this38 = this;
      this.container = document.createElement('ul');
      this.container.id = "autocomplete-options-" + M.guid();
      $(this.container).addClass('autocomplete-content dropdown-content');
      this.$inputField.append(this.container);
      this.el.setAttribute('data-target', this.container.id);

      this.dropdown = M.Dropdown.init(this.el, Object.assign({
         autoFocus: false,
         closeOnClick: false,
         coverTrigger: false,
         onItemClick: function (itemEl) {
            _this38.selectOption($(itemEl));
         }
      }, this.options.dropdownOptions || {}));

      // Sketchy removal of dropdown click handler
      this.el.removeEventListener('click', this.dropdown._handleClickBound);
   },

   _renderDropdown: function(data, val) {
      var _this39 = this;
      this._resetAutocomplete();
      if(!data || !data.length){
         this.close()
         return
      } else {
         this.isOpen = true
      }

      // Gather all matching data
      if (!this.options.customFilter) {
          this.filteredData = data.filter(o => {
            return o.label.toLowerCase().indexOf(val) !== -1
         })
      } else {
         this.filteredData = data
      }

      this.filteredData.splice(this.options.limit)
      this.count = this.filteredData.length

      // Sort
      if (this.options.sortFunction) {
         var sortFunctionBound = function(a, b) {
            return _this39.options.sortFunction(a.label.toLowerCase(), b.label.toLowerCase(), val.toLowerCase());
         };
         this.filteredData.sort(sortFunctionBound);
      }

      // Render
      this.filteredData.forEach((option, idx) => {
         var $autocompleteOption = $(`<li value="${option.value}" idx="${idx}"></li>`);
         option.img && $autocompleteOption.append("<img src=\"" + option.img + "\" class=\"right circle\">");
         $autocompleteOption.append(`<span>${option.label}</span><small class="info">${option.info || ""}</small>`);

         $(this.container).append($autocompleteOption);
         !this.options.customFilter && this._highlight(val, option, $autocompleteOption);
      })
      this.dropdown && this.dropdown.recalculateDimensions();
   },


   _highlight(string, option, $el) {
     var matchStart = option.label.toLowerCase().indexOf('' + string.toLowerCase() + ''),
         matchEnd = matchStart + string.length - 1,
         beforeMatch = option.label.slice(0, matchStart),
         matchText = option.label.slice(matchStart, matchEnd + 1),
         afterMatch = option.label.slice(matchEnd + 1);
      $el.empty()
      option.img && $el.append("<img src=\"" + option.img + "\" class=\"right circle\">");
      $el.append(`<span>${beforeMatch}<span class="highlight">${matchText}</span>${afterMatch}</span><small class="info">${option.info || ""}</small>`);
   },

   selectOption: function(el) {
      let option = this.filteredData[$(el).attr("idx")]
      this.el.value = option.label;
      this.$el.trigger('change');
      this._resetAutocomplete();
      this.close();

      // Handle onAutocomplete callback.
      if (typeof this.options.onAutocomplete === 'function') {
         this.options.onAutocomplete.call(this, option);
      }
   }
}

$.extend(M.Autocomplete.prototype, autocompleteExtension)



let dropdownExtension = {
   /* if scrollbar is displayed inside dropdown make it wider so rows wont get wrapped */
   _placeDropdown: function(){
      // Set width before calculating positionInfo
      var idealWidth = this.options.constrainWidth ? this.el.getBoundingClientRect().width : this.dropdownEl.getBoundingClientRect().width;
      this.dropdownEl.style.width = idealWidth + 'px';

      var positionInfo = this._getDropdownPosition();
      let hasScrollbar = this.dropdownEl.scrollHeight > positionInfo.height
      let scrollBarWidth = 17  // usually between 12-17px
      this.dropdownEl.style.left = positionInfo.x + 'px';
      this.dropdownEl.style.top = positionInfo.y + 'px';
      this.dropdownEl.style.height = positionInfo.height + 'px';
      this.dropdownEl.style.width = (positionInfo.width + (hasScrollbar ? scrollBarWidth : 0)) + 'px';
      this.dropdownEl.style.transformOrigin = (positionInfo.horizontalAlignment === 'left' ? '0' : '100%') + " " + (positionInfo.verticalAlignment === 'top' ? '0' : '100%');
   }
}
$.extend(M.Dropdown.prototype, dropdownExtension)



let tooltipExtension = {
   old_open: M.Tooltip.prototype.open,
   old_animateOut: M.Tooltip.prototype._animateOut,

   open: function(params){
      if(this.el.getAttribute('data-tooltip')?.trim() || this.options.html.trim()){
         this.old_open(params)
      }
   },

   _animateOut: function(){
      this.tooltipEl.removeEventListener("mouseenter", this._handleElMouseEnterBound)
      this.tooltipEl.removeEventListener("mouseleave", this._handleElMouseLeaveBound)
      this.old_animateOut()
      this.tooltipEl.style.pointerEvents = "none"
      this.onClose && this.onClose()
   }
}
$.extend(M.Tooltip.prototype, tooltipExtension)
