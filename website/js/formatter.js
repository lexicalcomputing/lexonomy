class FormatterClass{
   constructor(){
      this.numFormat = new Intl.NumberFormat("en", {})
      this.timeFormat = new Intl.DateTimeFormat("en", {hour: "numeric", minute: "numeric", second: "numeric"})
      this.dateTimeFormat = new Intl.DateTimeFormat("en", {year: "numeric", month: "long", day: "numeric", hour: "numeric", minute: "numeric", second: "numeric"})
   }

   num(num, options){
      if(num === "" || num === null || typeof num == "undefined"){
         return ""
      }
      if(options){
         if(typeof options == "number"){
            if(!this["numFormat" + options]){
               this["numFormat" + options] = new Intl.NumberFormat("en", {
                  minimumFractionDigits: options,
                  maximumFractionDigits: options
               })
            }
            return this["numFormat" + options].format(num)
         } else {
            return new Intl.NumberFormat("en", options).format(num)
         }
      }
      return this.numFormat.format(num);
   }

   date(dateObj, options){
      if(this._validDate(dateObj)){
         if(options){
            return new Intl.DateTimeFormat("en", options).format(dateObj)
         }
         //return this.dateFormat.format(dateObj)
         let y = new Intl.DateTimeFormat('en', { year: 'numeric' }).format(dateObj)
         let m = new Intl.DateTimeFormat('en', { month: 'long' }).format(dateObj)
         let d = new Intl.DateTimeFormat('en', { day: 'numeric' }).format(dateObj)
         return `${dateObj.getDate()} ${m} ${dateObj.getFullYear()}`
      }
   }

   shortDate(dateObj){
      if(this._validDate(dateObj)){
         let m = new Intl.DateTimeFormat('en', { month: 'long' }).format(dateObj)
         return `${(dateObj.getDate() + "").padStart(2, "0")} ${m.substr(0, 3)} ${dateObj.getFullYear()}`
      }
   }

   time(dateObj, options){
      if(this._validDate(dateObj)){
         return this.timeFormat.format(dateObj)
      }
   }

   dateTime(dateObj){
      if(this._validDate(dateObj)){
         return `${this.shortDate(dateObj)} at ${this.time(dateObj)}`
      }
   }

   address(addresses){
      if(!addresses){
         return ""
      }
      return addresses.map(address => {
         return `${address.address || ""}${address.address && address.country ? ", " : ""}${address.country || ""}`
      }).join("<br><br>")
   }

   _validDate(dateObj){
      return dateObj && !isNaN(dateObj.getTime())
   }

}

window.Formatter = new FormatterClass()
