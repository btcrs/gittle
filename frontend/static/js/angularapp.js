//
function dataURIToBlob(dataURI, callback) {
  var binStr = atob(dataURI.split(',')[1]),
    len = binStr.length,
    arr = new Uint8Array(len);

  for (var i = 0; i < len; i++) {
    arr[i] = binStr.charCodeAt(i);
  }

  callback(new Blob([arr]));
}

function b64toBlob(b64Data, contentType, sliceSize) {
  contentType = contentType || '';
  sliceSize = sliceSize || 512;

  var byteCharacters = atob(b64Data);
  var byteArrays = [];

  for (var offset = 0; offset < byteCharacters.length; offset += sliceSize) {
    var slice = byteCharacters.slice(offset, offset + sliceSize);

    var byteNumbers = new Array(slice.length);
    for (var i = 0; i < slice.length; i++) {
      byteNumbers[i] = slice.charCodeAt(i);
    }

    var byteArray = new Uint8Array(byteNumbers);

    byteArrays.push(byteArray);
  }

  var blob = new Blob(byteArrays, {type: contentType});
  return blob;
}



var verApp = angular.module('versioningApp', ['utf8-base64'])
.config( [
    '$compileProvider',
    function( $compileProvider )
    {   
        $compileProvider.aHrefSanitizationWhitelist(/^\s*(https?|mailto|data|blob):/);
        // Angular before v1.2 uses $compileProvider.urlSanitizationWhitelist(...)
    }
]);

verApp.directive('fileModel', ['$parse', function ($parse) {
    return {
       restrict: 'A',
       link: function(scope, element, attrs) {
          var model = $parse(attrs.fileModel);
          var modelSetter = model.assign;
          element.bind('change', function(){
             scope.$apply(function(){
                modelSetter(scope, element[0].files[0]);
             });
          });
       }
    };
}]);

verApp.service('fileUpload', ['$http', function ($http) {
    this.uploadFileToUrl = function(file, uploadUrl, path){
        var fd = new FormData();
        fd.append('file', file);
        // for sending manual values
        fd.append('path', path);
        $http.post(uploadUrl, fd, {
          transformRequest: angular.identity,
          headers: {'Content-Type': undefined}
        })
        .then(function(){
        })
        .catch(function(){
        });
    }
}]);


var baserUrl = 'http://localhost:8000'
// var baserUrl = 'https://test.wevolver.com'

verApp.controller('LoginCtrl',
    function($scope, $http, $window, base64, fileUpload)
    {
        $scope.baserUrl = baserUrl;
        $scope.tree = null;
        
        $scope.prevTreeId = null;
        $scope.file = null;
        $scope.repos = [];
        $scope.selectedRepo = null;
        $scope.user = localStorage.getItem("user_id");
        $scope.currentTreePath = [];
        $scope.treeIdPath = [];

        $scope.getRepos = function() {
            $http({
                method: 'GET',
                url: baserUrl + '/rodrigo',
                params: {
                    access_token: localStorage.getItem("access_token"),
                    user_id: localStorage.getItem("user_id"),
                }
            })
            .then( function (data, status, header) {
                // console.log(data);
                $scope.repos = data.data.data;
            })
        }

        $scope.selectRepo = function(repoName) {
            $scope.selectedRepo = repoName;
            $scope.getTree(null, 'tree')
        }

        $scope.createRepo = function() {
            $http({
                method: 'GET',
                url: baserUrl + '/create/rodrigo/' + $scope.repo_name,
                params: {
                    access_token: localStorage.getItem("access_token"),
                    user_id: localStorage.getItem("user_id"),
                }
            })
            .then( function (data, status, header) {
                // console.log(data);
                $scope.repos.push($scope.repo_name);
            })
        }

        $scope.deleteRepo = function(repoName) {
            $http({
                method: 'GET',
                url: baserUrl + '/delete/rodrigo/' + repoName,
                params: {
                    access_token: localStorage.getItem("access_token"),
                    user_id: localStorage.getItem("user_id"),
                }
            })
            .then( function (data, status, header) {
                // console.log(data);
                var index = $scope.repos.indexOf(repoName);
                if (index > -1) {
                    $scope.repos.splice(index, 1);
                }
            })
        }

        $scope.getTree = function(oid, type, filename) {
            var oid_param = '';
            $scope.file = null;

            if (oid) {
                oid_param = '/' + oid;
                if(type == 'tree') {
                    // $scope.prevTreeId = $scope.treeId;
                    // $scope.treeId = oid;
                    console.log(filename)
                    if(filename === undefined) {
                        $scope.currentTreePath.pop();
                        $scope.treeIdPath.pop();
                    } else {
                        $scope.currentTreePath.push(filename);
                        $scope.treeIdPath.push(oid);
                    }

                }
            } else {
                if(type == 'tree') {
                    // $scope.prevTreeId = null;
                    // $scope.treeId = null;
                    $scope.treeIdPath = [];
                    $scope.currentTreePath = [];
                }
            }
            if($scope.treeIdPath.length > 1) {
                $scope.prevTreeId = $scope.treeIdPath[$scope.treeIdPath.length - 2]
            } else {
                $scope.prevTreeId = null;
            }

            $http({
                method: 'GET',
                url: baserUrl + '/rodrigo/' + $scope.selectedRepo + oid_param,
                params: {
                    access_token: localStorage.getItem("access_token"),
                    user_id: localStorage.getItem("user_id"),
                }
            })
            .then( function (data, status, header) {
                if(type == 'tree') {
                    $scope.tree = data.data.data;
                } else {

                    var extension = filename.split('.').pop();
                    $scope.fileSrc = null;
                    $scope.fileName = filename;
                    $scope.fileType = '';

                    if(['jpg', 'jpeg', 'png', 'tiff', 'gif', 'bmp'].indexOf(extension) > -1) {
                        $scope.fileSrc = 'data:image/' + extension + ';charset=utf-8;base64, ' + data.data.file;
                        $scope.fileType = 'image';

                        var blob = b64toBlob(data.data.file, 'image/' + extension);
                        var url = URL.createObjectURL(blob);
                        $scope.fileAttachment = url;
                        // if (navigator.msSaveBlob) { // IE 10+
                        //     navigator.msSaveBlob(blob, filename);
                        // } else {

                        $scope.fileSrc = url;

                    } else {
                        var blob = b64toBlob(data.data.file, 'text/' + extension);
                        $scope.fileSrc = base64.urldecode(data.data.file);
                        $scope.fileType = 'text';
                        $scope.fileAttachment = 'data:attachment/charset=utf-8;base64, ' + data.data.file;
                    }
                }

            })
        }
        var isLoggedIn = function() {
            if($scope.user) {
                $scope.getRepos();
            }
        }
        isLoggedIn();

        $scope.submit = function()
        {
            var data = {
                username: $scope.email,
                password: $scope.password,
            };

            var req = {
                method: 'POST',
                url: baserUrl + '/login',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data: data,
            }
            if (data.username && data.password) {
                $http(req)
                .then(function (data, status, headers) {

                    localStorage.setItem("access_token", data.data.access_token);
                    localStorage.setItem("client_id", data.data.client_id);
                    localStorage.setItem("client_secret", data.data.client_secret);
                    localStorage.setItem("refresh_token", data.data.refresh_token);

                    var user_id = data.data.user ? data.data.user.split('/') : null;

                    user_id = user_id ? user_id[user_id.length - 2] : '';

                    localStorage.setItem("user_id", user_id);

                    $scope.user = user_id;

                    if($scope.user) {
                        $scope.getRepos();
                    }
                }, function (data, status, header) {
                    $scope.ResponseDetails = "Couldn't log in";
                });
            }

        };
        
        $scope.signout = function()
        {
            localStorage.clear();
            $scope.user = false;
        }

        $scope.downloadArchive = function(project_name)
        {
            window.location = baserUrl + '/rodrigo/' + project_name
            + '/archive?access_token=' + localStorage.getItem("access_token")
            + '&user_id=' + localStorage.getItem("user_id")
        }   
        $scope.createFolder = function() {
            var path = $scope.currentTreePath;//.push($scope.folder_name);
            //$scope.currentTreePath.pop();
            path.push($scope.folder_name)

            console.log(path)
            var req = {
                method: 'POST',
                url: baserUrl + '/rodrigo/' + $scope.selectedRepo + '/newfolder?access_token=' + localStorage.getItem("access_token")
                + '&user_id=' + localStorage.getItem("user_id"),
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data: {path: path},
            }
            if($scope.folder_name) {
                $http(req)
                .then(function() {
                    path.pop()
                })
            }
        }

        $scope.uploadFile = function(){
           var file = $scope.fileToUpload;
           var path = $scope.currentTreePath;
           var uploadUrl = baserUrl + '/rodrigo/' + $scope.selectedRepo + '/upload?access_token=' + localStorage.getItem("access_token")
            + '&user_id=' + localStorage.getItem("user_id");
           fileUpload.uploadFileToUrl(file, uploadUrl, path);
        };
    });