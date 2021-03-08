function giveResult(text)
    {
        let p = document.createElement('p');
        p.innerHTML = text;
        return p;
    }

    let form = document.forms[0];
    let result = document.getElementById('result');


    form.addEventListener('submit', (event) => {
        //Берём данные из формы
        let data = {
            login: form[0].value,
            password: form[1].value
        }

        let xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/login', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify(data));

            xhr.onreadystatechange = function() {
        if (xhr.readyState != 4) {
                return;
        }

        result.innerHTML = '';
        if (xhr.status === 200) {
            result.append(giveResult(xhr.responseText));
            setTimeout(() => {
                window.location.replace('/index');
            }, 1500);
           
        } else {
            let response = JSON.parse(xhr.responseText);
            result.append(giveResult(response.detail));
        }
        }

        // //Проверяем данные из формы
        // let response  = fetch('http://127.0.0.1:5000/api/login', {
        //     method: 'POST',
        //     headers: {
        //         'Accept': 'application/json, text/plain',
        //         'Content-Type': 'application/json'
        //     },
        //     body: JSON.stringify(data)
        // });
        
        // console.dir(promise);

        
        event.preventDefault();
    });
    
