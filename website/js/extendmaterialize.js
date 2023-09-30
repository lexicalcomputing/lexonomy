let autocompleteExtension = {
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
            return _this39.options.sortFunction(a.value.toLowerCase(), b.value.toLowerCase(), val.toLowerCase());
         };
         this.filteredData.sort(sortFunctionBound);
      }

      // Render
      this.filteredData.forEach((option, idx) => {
         var $autocompleteOption = $(`<li value="${option.value}" idx="${idx}"></li>`);
         option.img && $autocompleteOption.append("<img src=\"" + option.img + "\" class=\"right circle\">");
         $autocompleteOption.append(`<span style="padding: 10px 16px;">${option.label}<small class="grey-text right">${option.info || ""}</small></span>`);

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
      $el.append(`<span style="padding: 10px 16px;">${beforeMatch}<span class="highlight">${matchText}</span>${afterMatch}<small class="grey-text right">${option.info || ""}</small></span>`);
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
