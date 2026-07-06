from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

ARQUIVO = "agendamentos.json"


def carregar():
    if os.path.exists(ARQUIVO):
        try:
            with open(ARQUIVO, "r", encoding="utf-8") as f:
                lista = json.load(f)

                for a in lista:
                    if "id" not in a:
                        a["id"] = lista.index(a) + 1

                    if "duracao" not in a:
                        a["duracao"] = 30

                return lista

        except:
            return []

    return []


def salvar(lista):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=4)


def duracao_servico(servico):

    tempos = {
        "Corte": 30,
        "Barba": 15,
        "Corte + Barba": 40,
        "Corte + Sobrancelha": 35,
        "Corte + Pigmentação": 60
    }

    return tempos.get(servico, 30)


@app.route("/")
def inicio():

    lista = carregar()

    lista.sort(key=lambda x: (x["data"], x["hora"]))

    agenda = ""

    for a in lista:

        data = datetime.strptime(
            a["data"],
            "%Y-%m-%d"
        ).strftime("%d/%m/%Y")

        agenda += f"""
        <div class="ag">
        👤 <b>{a['nome']}</b><br>
        📅 {data}<br>
        🕒 {a['hora']}<br>
        ✂️ {a['servico']}<br>
        ⏱️ {a['duracao']} minutos<br><br>

        <button onclick="cancelar({a['id']})">
        Cancelar
        </button>

        <button onclick="editar({a['id']})">
        Editar
        </button>

        </div>
        """

    return """
    
    <!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">

<title>Barbearia Regys</title>

<style>

body{
margin:0;
font-family:Arial;
background-image:url(
"https://images.unsplash.com/photo-1621605815971-fbc98d665033"
);
background-size:cover;
background-position:center;
color:white;
display:flex;
justify-content:center;
padding:20px;
}


.caixa{

background:rgba(0,0,0,0.85);
width:380px;
padding:25px;
border-radius:20px;

}


input,select,button{

width:100%;
padding:12px;
margin-top:10px;
border-radius:8px;
border:none;

}


button{

background:#d4af37;
font-weight:bold;
cursor:pointer;

}


.ag{

background:#333;
padding:15px;
margin-top:15px;
border-radius:10px;

}


h1,h2{

text-align:center;
color:#d4af37;

}

</style>

</head>


<body>


<div class="caixa">


<h1>💈 Barbearia Regys</h1>


<input id="nome" placeholder="Nome">


<select id="servico">

<option>Corte</option>
<option>Barba</option>
<option>Corte + Barba</option>
<option>Corte + Sobrancelha</option>
<option>Corte + Pigmentação</option>

</select>


<input id="data" type="date">


<input id="hora" type="time">


<button onclick="agendar()">
AGENDAR
</button>


<h2>📋 Agenda</h2>


""" + agenda + """


</div>



<script>


function agendar(){

fetch("/agendar",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

nome:nome.value,

servico:servico.value,

data:data.value,

hora:hora.value

})

})

.then(r=>r.json())

.then(r=>{

alert(r.mensagem);

location.reload();

});

}



function cancelar(id){

if(confirm("Cancelar agendamento?")){

fetch("/cancelar/"+id,{

method:"DELETE"

})

.then(r=>r.json())

.then(r=>{

alert(r.mensagem);

location.reload();

});

}

}



function editar(id){

let novoNome = prompt("Novo nome:");

if(novoNome){

fetch("/editar/"+id,{

method:"PUT",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

nome:novoNome

})

})

.then(r=>r.json())

.then(r=>{

alert(r.mensagem);

location.reload();

});

}

}



</script>


</body>

</html>

"""

@app.route("/agendar", methods=["POST"])
def agendar():

    dados = request.json

    lista = carregar()

    duracao = duracao_servico(
        dados["servico"]
    )


    inicio = datetime.strptime(
        dados["data"] + " " + dados["hora"],
        "%Y-%m-%d %H:%M"
    )


    fim = inicio + timedelta(
        minutes=duracao
    )


    if inicio.hour < 11 or fim.hour > 17:

        return jsonify({
            "mensagem":"Fora do horário de funcionamento"
        })


    for a in lista:

        inicio2 = datetime.strptime(
            a["data"] + " " + a["hora"],
            "%Y-%m-%d %H:%M"
        )


        fim2 = inicio2 + timedelta(
            minutes=a["duracao"]
        )


        if inicio < fim2 and fim > inicio2:

            return jsonify({
                "mensagem":"Horário já ocupado"
            })


    novo_id = 1

    if lista:

        novo_id = max(
            a["id"] for a in lista
        ) + 1


    dados["id"] = novo_id

    dados["duracao"] = duracao


    lista.append(dados)

    salvar(lista)


    return jsonify({
        "mensagem":"Agendamento realizado!"
    })




@app.route("/cancelar/<int:id>", methods=["DELETE"])
def cancelar(id):

    lista = carregar()


    lista = [
        a for a in lista
        if a["id"] != id
    ]


    salvar(lista)


    return jsonify({
        "mensagem":"Agendamento cancelado!"
    })




@app.route("/editar/<int:id>", methods=["PUT"])
def editar(id):

    dados = request.json

    lista = carregar()


    for a in lista:

        if a["id"] == id:

            a["nome"] = dados["nome"]


    salvar(lista)


    return jsonify({
        "mensagem":"Agendamento editado!"
    })




if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=False
    )