// Write your Javascript code

function isValidURL(string) {
    var res = string.match(/(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)/g);
    return (res !== null)
};


function alert_bs(message, type) {
    var div = $('<div></div>').html(message).attr('class', 'text-' + type.toLowerCase());
    $('#messageModal .modal-body').html(div);
    $('#messageModal').modal('show');    
}

function raiseApiValidationError(errors) {
    errList = [];
    for (var i in errors) {
        type = errors[i];
        for (var j in type) {
            errList.push(j.toUpperCase() + ': ' + type[j]);
        }
    }
    alert_bs(errList.join('<br/>'), 'danger');
}