var app = angular.module("searchApp", []);

app.directive('loading',   ['$http' ,function ($http)
 {
     return {
         restrict: 'A',
         //template: '<div class="loading-spiner"><img src="http://www.nasa.gov/multimedia/videogallery/ajax-loader.gif" /> </div>',
           template: '<div class="loading-spiner"><img src="https://media.giphy.com/media/52qtwCtj9OLTi/giphy.gif" /> </div>',
         link: function (scope, elm, attrs)
         {
             scope.isLoading = function () {
                 return $http.pendingRequests.length > 0;
             };

             scope.$watch(scope.isLoading, function (v)
             {
                 if(v){
                     elm.show();
                 }else{
                     elm.hide();
                 }
             });
         }
     };
 }])

  app.factory('logTimeTaken', [function() {
    var logTimeTaken = {
        request: function(config) {
            config.requestTimestamp = new Date().getTime();
            return config;
        },
        response: function(response) {
            response.config.responseTimestamp = new Date().getTime();
            return response;
        }
    };
    return logTimeTaken;
}]);
app.config(['$httpProvider', function($httpProvider) {
    $httpProvider.interceptors.push('logTimeTaken');
}]);

app.controller("searchController", function($scope, $http) {
        $scope.CurrentDate = new Date();
		$scope.querylist= []
		$scope.answerlist = []
		$scope.counter = 0
  $scope.getRequest = function() {
    console.log("I've been pressed!");
    $scope.querylist.push($scope.query)
    $scope.counter = $scope.counter + 1
    console.log($scope.counter)
    $http.get("/search/doQuery?keyword="+$scope.query).then(
      function successCallback(response) {
      console.log(response.data.result)
		$scope.searchdata=response.data.result.answer;
		$scope.link=response.data.result.link;
		$scope.available=response.data.result.available;
		$scope.show = false;
		$scope.answerlist.push($scope.searchdata)
		$scope.time = response.config.responseTimestamp - response.config.requestTimestamp;
		$scope.rtime = $scope.time/1000
        console.log('Time taken ' + ($scope.rtime) + ' seconds.');
		//alert($scope.counter)
		//$scope.querylist.push({'question':$scope.query,'answer':$scope.searchdata})

      },
      function errorCallback(response) {
        console.log("Unable to perform get request");
        $scope.answerlist.push('Sorry Error Occurred')
      }
    );
  };

    $scope.talk = function(query) {
         $scope.chat=[]
         $scope.chatquery= []
         $scope.answer = getRequest()
         $scope.chat.push(answer)
         $scope.chatquery.push(query)
         console.log("Checking...")
         console.log(chat)
//         var user = document.getElementById("userBox").value;
//         document.getElementById("userBox").value = "";
//         document.getElementById("msg_history").innerHTML += user+"<br>";
//         if (getRequest()) {
//            document.getElementById("msg_history").innerHTML += know[user]+"<br>";
//         } else {
//            document.getElementById("msg_history").innerHTML += "I don't understand...<br>";
//             }
         }

    $scope.loadQuestions = function() {
    $http.get("/search/getQuestions").then(
      function successCallback(response) {
        //data = JSON.parse(response.data);
        $scope.questions = [];
		$scope.questions=response.data.q;
		if($scope.questions.length > 0){
		   $scope.hidethis = false;
		} else{
		    $scope.hidethis = true;
		}

		console.log($scope.questions)
      },
      function errorCallback(response) {
        console.log("Unable to perform get request");
      }
    );
  };
  $scope.complete = function(string){
           $scope.hidethis = false;
           var output = [];
           angular.forEach($scope.questions, function(question){
                if(question.toLowerCase().indexOf(string.toLowerCase()) >= 0)
                {
                     output.push(question);
                }
           });
      $scope.filterQuestion = output;
	//  console.log(output)
      }
   $scope.fillTextbox = function(d){
        //   $scope.query = "";
           $scope.query = d;
           $scope.questions = [];
           console.log("hi")
           $scope.hidethis = true;
      };
      $scope.findString =function(text){
          alert("String \x22" + text + "\x22 found? " + window.find(text));
    }


    $scope.showPdf=function(link){
        document.getElementById('frame').style.display='block'
        document.getElementById('render').src='http://localhost:8888/web/viewer.html?file=Draft_HZL_O2C_SOP_(Metal_Sales).pdf#search='+link+'&phrase=true'
		//document.getElementById('render').src='http://localhost:8888/web/viewer.html?file='+link
    }
    $scope.closePdf=function(){
      // $scope.frameid = document.getElementById("frame");
       $scope.frameid = document.getElementById('frame').style.display = 'none';


     // $scope.parent = frameid.parentNode.removeChild(frameid);
    }
    $scope.findtext = function(text){
        document.getElementById('frame').contents().find(text).style.color="yellow"
    }

// $scope.complete=function(){
//    $( "#questions" ).autocomplete({
//      source: $scope.questions
//    });
//    }
}).config(function($interpolateProvider) {
        $interpolateProvider.startSymbol('//').endSymbol('//');
 });