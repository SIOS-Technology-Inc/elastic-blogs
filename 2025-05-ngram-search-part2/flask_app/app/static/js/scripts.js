
function show_detail(elements) {
    var detail = "";
    if (elements != null && elements.length > 0) {
        detail = "code: " + elements[0].value + "\nname: " + elements[0].innerHTML;                 
    }
    document.getElementById('detail_info').innerText = detail;
}

function search_medicine() {
    value1 = document.getElementById('hidden1').value;
    value2 = document.getElementById('hidden2').value;

    if (value1.length < 2) {
        if (value2.length < 2) {
            select1 = '<select name="select1" size="1">\n'
            + '<option value="">---</option>\n'
            + '</select>'
            document.getElementById('search_results').innerHTML = select1;
            document.getElementById('detail_info').innerText = "";
            return;
        } else {
            // only value2
            value1 = value2;
            value2 = '';
        }
    } else if (value2.length < 2) {
        // only value1
        value2 = '';
    }

    // ajax 通信を行う。
    fetch('/search_medicine',
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 'search_medicine_name1': value1, 'search_medicine_name2': value2 })
        }
    ).then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('error');
            console.error(data);
        } else {
            data_size = data.length + 1;

            if (data_size > 30) {
                data_size = 30
            }

            select1 = '<select name="select1" size="' + data_size + '" onchange="show_detail(this.selectedOptions)">\n';
            select1 += '<option value="">---</option>\n'

            data.forEach(element => {
                select1 += '<option value="' + element.medicine_code + '">' + element.medicine_name + '</option>\n'
            });
            select1 += '</select>'
            document.getElementById('search_results').innerHTML = select1;
        }
    })
}

function onkeyup1(value1) {
    changed = false;
    hidden1 = document.getElementById('hidden1');
    org_value1 = hidden1.value;
    if (value1.length < 2) {
        if (org_value1.length > 1) {
            hidden1.value = '';
            changed = true
        } 
    } else {
        if (org_value1 != value1) {
            hidden1.value = value1;
            changed = true
        }
    }

    if (changed) {
        search_medicine()
    }
}

function onkeyup2(value2) {
    changed = false;
    hidden2 = document.getElementById('hidden2');
    org_value2 = hidden2.value;
    if (value2.length < 2) {
        if (org_value2.length > 1) {
            hidden2.value = '';
            changed = true
        } 
    } else {
        if (org_value2 != value2) {
            hidden2.value = value2;
            changed = true
        }
    }

    if (changed) {
        search_medicine()
    }
}

