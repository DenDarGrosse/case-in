function createButton(text, nameQuery)
{
    let button = document.createElement('button');
    button.setAttribute('type', 'button');
    button.setAttribute('class', "btn btn-primary btn-lg");
    button.setAttribute('onclick', "clickOnButtonQuery(this)");
    button.setAttribute('data-query', nameQuery);
    button.innerHTML = nameQuery;

    return button;
}

//Блок построения таблицы
var _table_ = document.createElement('table'),
_tr_ = document.createElement('tr'),
_th_ = document.createElement('th'),
_td_ = document.createElement('td');
_table_.setAttribute('class', 'table');

// Builds the HTML Table out of myList json data from Ivy restful service.
function buildHtmlTable(arr) 
{
    var table = _table_.cloneNode(false),
    columns = addAllColumnHeaders(arr, table);
    for (var i = 0, maxi = arr.length; i < maxi; ++i) {
        var tr = _tr_.cloneNode(false);
        for (var j = 0, maxj = columns.length; j < maxj; ++j) {
            var td = _td_.cloneNode(false);
            cellValue = arr[i][columns[j]];
            td.appendChild(document.createTextNode(arr[i][columns[j]] || ''));
            tr.appendChild(td);
        }
        table.appendChild(tr);
    }
    return table;
}

function addAllColumnHeaders(arr, table) 
{
    var columnSet = [],
    tr = _tr_.cloneNode(false);
    for (var i = 0, l = arr.length; i < l; i++) {
        for (var key in arr[i]) {
            if (arr[i].hasOwnProperty(key) && columnSet.indexOf(key) === -1) {
                columnSet.push(key);
                var th = _th_.cloneNode(false);
                th.appendChild(document.createTextNode(key));
                tr.appendChild(th);
            }
        }
    }
    table.appendChild(tr);
    return columnSet;
} 
///Конец блока

function clickOnButtonQuery(button)
{
    //Формируем данные для отправки
    let data = 
    {
    "args_arr": "",
    "request_name": button.dataset.query
    }

    //Делаем запрос
    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/request', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify(data));

    xhr.onreadystatechange = function() {
            if (xhr.readyState == 3 && xhr.status == 200) {
                resultQuery.innerHTML = "<p>Вывод результата запроса:</p>" 
                resultQuery.appendChild(buildHtmlTable(JSON.parse(xhr.responseText)));
            }
    }   

}



//Инициализация переменных
let resultQuery = document.getElementById('resultQuery');
let tbody = document.getElementById('tbody');
let blockButton = document.getElementById('blockButton');
let result = document.getElementById('result');

//Получаем массив доступных запросов для пользователя
let xhr = new XMLHttpRequest();
xhr.open('GET', '/api/request', false);
xhr.setRequestHeader('Accept', 'application/json');
xhr.send();

xhr.onreadystatechange = function() {
if (xhr.readyState != 4) {
        return;
    }
}

let ArrayObject = JSON.parse(xhr.responseText);

//Перебираем запросы добавляю кнопки
ArrayObject.forEach(element => {
let keys = Object.keys(element);
blockButton.append(createButton(element[keys], keys));
}); 