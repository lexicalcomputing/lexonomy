class ConnectionClass {
   constructor(){
      observable(this)
   }

   get(params){
      if(typeof params == "string"){
         return this.sendRequest(Object.assign({
            url: params,
            method: "GET"
         }))
      } else {
         return this.sendRequest(Object.assign({
            method: "GET"
         }, params))
      }
   }

   post(params){
      return this.sendRequest(Object.assign({
         method: "POST"
      }, params))
   }

   sendRequest(params){
      return $.ajax(params)
            .done(response => {
               if(response.loggedin === false || response.userAccess === false){
                  window.auth.invalidateSession()
               }
            })
   }
}

window.connection = new ConnectionClass()
