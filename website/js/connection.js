class ConnectionClass {
   constructor(){
      observable(this)
      $.ajaxSetup({
         xhrFields: {
            withCredentials: true
         }
      })
   }

   get(params){
      return this.sendRequest(Object.assign({
         method: "GET"
      }, params))
   }

   post(params){
      return this.sendRequest(Object.assign({
         method: "POST"
      }, params))
   }

   sendRequest(params){
      let failMessage = params.failMessage || ""
      let successMessage = params.successMessage || ""
      delete params.failMessage
      delete params.successMessage
      return $.ajax(params)
            .done(response => {
               if(response.loggedin === false){
                  window.auth.invalidateSession()
               }
            })
            .always(this.notifyAboutRequestResult(failMessage, successMessage))
   }

   notifyAboutRequestResult(failMessage, sucessMessage){
      return function(failMessage, sucessMessage, response) {
         if(failMessage){
            if(response){
               if(response.error){
                  window.showToast(`${failMessage}\n${response.error}`)
               } else if(typeof response.statusText != "undefined" && response.statusText != "abort"){
                  window.showToast(`${failMessage}\n${response.statusText || ""}`)
               }
            } else {
               window.showToast(failMessage)
            }
         }
         if(sucessMessage && response && !response.error){
            M.toast({html: sucessMessage})
         }
      }.bind(this, failMessage, sucessMessage)
   }
}

window.connection = new ConnectionClass()
