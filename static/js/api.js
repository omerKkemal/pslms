var loc = location.origin
var endPointes = [//lenget 12 or 11 <-- (index start at 0)
    '/admin/panal/add_students',
    '/admin/panal/add_student/',// need grade and section(parmeter: section and grade)
    '/admin/panal/info/',// get section and grade info or list of theachers(parmater: teacher or student)
    '/admin/panal/get_students/',// get list of student(parmeter: section and grade)
    '/admin/panal/update_student/',// update student info by studentID(parmetr: id)
    '/admin/panal/add_teacher',
    '/admin/panal/get_teachers',
    '/admin/panal/add_subject_to_teacher/',// add subject to teacher(parmetr: id)
    '/admin/panal/edit_teacher_info/',// edit basic info teacher(parmetr: id)
    '/admin/panal/delete_student',// delete student by ID(parmetr: id)
    '/admin/panal/delete_teacher',// delete teacher by ID(parmetr: id)
    '/admin/panal/delete_resource'
]

// Delete
function flaskApi_Delete(ID, index) {
    var url = loc + endPointes[Number(index)];
    console.log(url);
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ 'id': ID }),
    })
    .then(response => {
        if (response.ok) {
            hidePageLoader();
            showNotification('Deleted successfully', 'success');
            setTimeout(() => location.reload(), 1200);
        } else {
            hidePageLoader();
            showNotification('Something went wrong. Try again.', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hidePageLoader();
        showNotification('Network error. Try again.', 'error');
    });
}

// Add Student
function flaskAddStudent(){
    showPageLoader();
    var fname = document.forms['addStudents']['fname'].value;
    var mname = document.forms['addStudents']['mname'].value;
    var lname = document.forms['addStudents']['lnmae'].value;
    var grade = document.forms['addStudents']['grade'].value;
    var gender = document.forms['addStudents']['gender'].value;
    var section = document.forms['addStudents']['section'].value;
    var url = loc + endPointes[0];
    var data = {
        'fname': fname,
        'mname': mname,
        'lname': lname,
        'grade': grade,
        'gender': gender,
        'section': section,
    }
    fetch(url,{
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(data),
    })
    .then(response => {
        if(response.ok){
            console.log(response);
            hidePageLoader();
            notifcation('Student was add successfully! ^_^','green');
            return true;
        } else {
            console.error(response);
            hidePageLoader();
            notifcation('Somting went Wrong :( Try again...')
            return false;
        }
    })
    .catch(error => {
        console.error(error);
        hidePageLoader();
        notifcation('Somting went Wrong :( Try again...')
        return false;
    });
}

function _delete(ID,index) {
    var Delete = confirm('Are you sure you want to delete this student?');
    if (Delete) {
        showPageLoader();
        flaskApi_Delete(ID,index);

    }else{
        notifcation('Canciling deletion!!!!!');
        return;
    }
}