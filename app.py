from flask import Flask, request, jsonify, session
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

app.secret_key = "chave_barbearia_regys"

ARQUIVO = "agendamentos.json"

SENHA_BARBEIRO = "019283"


def carregar():

    if os.path.exists(ARQUIVO):

        try:

            with open(
                ARQUIVO,
                "r",
                encoding="utf-8"
            ) as f:

                lista = json.load(f)


            for i, ag in enumerate(lista):

                if "id" not in ag:
                    ag["id"] = i + 1

                if "duracao" not in ag:
                    ag["duracao"] = 30


            return lista


        except:

            return []


    return []



def salvar(lista):

    with open(
        ARQUIVO,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            lista,
            f,
            ensure_ascii=False,
            indent=4
        )



def duracao_servico(servico):

    tempos = {

        "Corte": 30,

        "Barba": 15,

        "Corte + Barba": 40,

        "Corte + Sobrancelha": 35,

        "Corte + Pigmentação": 60,

        "🍽️ Horário de almoço": 40

    }

    return tempos.get(servico,30)



def horario_ocupado(
    novo_inicio,
    novo_fim,
    lista
):

    for ag in lista:

        inicio = datetime.strptime(
            ag["data"] + " " + ag["hora"],
            "%Y-%m-%d %H:%M"
        )

        fim = inicio + timedelta(
            minutes=ag["duracao"]
        )


        if novo_inicio < fim and novo_fim > inicio:

            return True


    return False
    @app.route("/")
def inicio():

    lista = carregar()

    lista.sort(
        key=lambda x: (
            x["data"],
            x["hora"]
        )
    )

    agenda = ""

    for a in lista:

        data = datetime.strptime(
            a["data"],
            "%Y-%m-%d"
        ).strftime("%d/%m/%Y")


        botoes = ""

        if session.get("barbeiro"):

            botoes = f"""
            <button onclick="cancelar({a['id']})">
            Cancelar
            </button>

            <button onclick="editar({a['id']})">
            Editar
            </button>
            """


        agenda += f"""

<div class="ag">

👤 <b>{a['nome']}</b><br>
📅 {data}<br>
🕒 {a['hora']}<br>
✂️ {a['servico']}<br>
⏱️ {a['duracao']} minutos

<br><br>

{botoes}

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


<hr>


<h2>🔒 Área do barbeiro</h2>

<input id="senha" type="password" placeholder="Senha">

<button onclick="login()">
Entrar
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



function login(){

fetch("/login",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

senha:senha.value

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

.then(()=>location.reload());

}

}



function editar(id){

let nomeNovo = prompt("Novo nome:");

if(nomeNovo){

fetch("/editar/"+id,{

method:"PUT",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

nome:nomeNovo

})

})

.then(()=>location.reload());

}

}

</script>


</body>

</html>

"""

@app.route("/login", methods=["POST"])
def login():

    dados = request.json

    if dados["senha"] == SENHA_BARBEIRO:

        session["barbeiro"] = True

        return jsonify({
            "mensagem":
            "Acesso liberado!"
        })


    return jsonify({
        "mensagem":
        "Senha incorreta!"
    })



@app.route("/agendar", methods=["POST"])
def agendar():

    dados = request.json

    nome = dados["nome"].strip()


    # Regra especial:
    # somente "Regys do corte"
    # vira horário de almoço

    if nome.lower() == "regys do corte":

        dados["servico"] = "🍽️ Horário de almoço"



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


    # Expediente 11:00 até 17:00

    if inicio.hour < 11 or fim.hour > 17:

        return jsonify({
            "mensagem":
            "Fora do horário de funcionamento"
        })


    if horario_ocupado(
        inicio,
        fim,
        lista
    ):

        return jsonify({
            "mensagem":
            "Horário já ocupado"
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

        "mensagem":
        "Agendamento realizado!"

    })




@app.route("/cancelar/<int:id>", methods=["DELETE"])
def cancelar(id):

    if not session.get("barbeiro"):

        return jsonify({
            "mensagem":
            "Acesso negado"
        })


    lista = carregar()


    lista = [
        a for a in lista
        if a["id"] != id
    ]


    salvar(lista)


    return jsonify({

        "mensagem":
        "Agendamento cancelado!"

    })




@app.route("/editar/<int:id>", methods=["PUT"])
def editar(id):

    if not session.get("barbeiro"):

        return jsonify({
            "mensagem":
            "Acesso negado"
        })


    dados = request.json

    lista = carregar()


    for a in lista:

        if a["id"] == id:

            a["nome"] = dados["nome"]



    salvar(lista)


    return jsonify({

        "mensagem":
        "Agendamento editado!"

    })




if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=False
    )
    
