from flask import Flask, request, jsonify, session, render_template
from datetime import datetime, timedelta
import json
import os

from twilio.rest import Client


app = Flask(__name__)

app.secret_key = "chave_barbearia_regys"


ARQUIVO = "agendamentos.json"

SENHA_BARBEIRO = "019283"



# ==========================
# TWILIO WHATSAPP
# ==========================

TWILIO_ACCOUNT_SID = "ACe9942ef12ce66b6afe0232c9d4807163"

TWILIO_AUTH_TOKEN = "ba6192efaaf69b3a7e81a4c3ce3c7277"

WHATSAPP_ORIGEM = "whatsapp:+14155238886"

WHATSAPP_DESTINO = "whatsapp:+5524999351341"



def enviar_whatsapp(mensagem):

    try:

        client = Client(
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN
        )

        envio = client.messages.create(

            from_=WHATSAPP_ORIGEM,

            body=mensagem,

            to=WHATSAPP_DESTINO

        )

        print("SID DO WHATSAPP:", envio.sid)


    except Exception as erro:

        print("ERRO TWILIO:", erro)




# ==========================
# CARREGAR AGENDAMENTOS
# ==========================

def carregar():

    if os.path.exists(ARQUIVO):

        try:

            with open(
                ARQUIVO,
                "r",
                encoding="utf-8"
            ) as arquivo:

                lista = json.load(arquivo)


            for i, ag in enumerate(lista):

                if "id" not in ag:

                    ag["id"] = i + 1


                if "duracao" not in ag:

                    ag["duracao"] = 30


            return lista


        except:

            return []


    return []





# ==========================
# SALVAR AGENDAMENTOS
# ==========================

def salvar(lista):

    with open(
        ARQUIVO,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(

            lista,

            arquivo,

            ensure_ascii=False,

            indent=4

        )
        
# ==========================
# LIMPAR AGENDAMENTOS PASSADOS
# ==========================

def limpar_agendamentos_antigos():

    lista = carregar()

    hoje = datetime.now().date()


    nova_lista = []


    for ag in lista:

        try:

            data_ag = datetime.strptime(
                ag["data"],
                "%Y-%m-%d"
            ).date()


            if data_ag >= hoje:

                nova_lista.append(ag)


        except:

            pass


    salvar(nova_lista)





# ==========================
# SERVIÇOS E DURAÇÕES
# ==========================

def servicos():

    return {

        "Cabelo": 30,

        "Barba": 15,

        "Cabelo e barba": 45,

        "Cabelo e sobrancelha": 35,

        "Cabelo e pigmentação": 60,

        "Cabelo, barba e pigmentação": 60,

        "🍽️ Horário de almoço": 40

    }




def duracao_servico(nome):

    return servicos().get(

        nome,

        30

    )





# ==========================
# VERIFICAR CONFLITO
# ==========================

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

            minutes=ag.get(

                "duracao",

                30

            )

        )


        if novo_inicio < fim and novo_fim > inicio:

            return True


    return False





# ==========================
# PÁGINA PRINCIPAL
# ==========================

@app.route("/")
def inicio():

    limpar_agendamentos_antigos()


    lista = carregar()


    lista.sort(

        key=lambda x:(

            x["data"],

            x["hora"]

        )

    )


    return render_template(

        "index.html",

        agenda=lista,

        barbeiro=session.get("barbeiro")

    )





# ==========================
# LOGIN BARBEIRO
# ==========================

@app.route("/login", methods=["POST"])
def login():

    dados = request.json


    if dados.get("senha") == SENHA_BARBEIRO:


        session["barbeiro"] = True


        return jsonify({

            "mensagem":
            "Modo barbeiro ativado!"

        })


    return jsonify({

        "mensagem":
        "Senha incorreta!"

    })





# ==========================
# DESLIGAR BARBEIRO
# ==========================

@app.route("/logout", methods=["POST"])
def logout():

    session.pop(

        "barbeiro",

        None

    )


    return jsonify({

        "mensagem":
        "Modo barbeiro desligado!"

    })
    
# ==========================
# CRIAR AGENDAMENTO
# ==========================

@app.route("/agendar", methods=["POST"])
def agendar():

    dados = request.json


    if not dados:

        return jsonify({

            "mensagem":
            "Dados inválidos"

        })



    nome = dados.get("nome","").strip()


    if nome == "":

        return jsonify({

            "mensagem":
            "Digite o nome"

        })



    # Regra do almoço

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



    # Expediente 11:00 às 18:00

    abertura = inicio.replace(

        hour=11,

        minute=0

    )


    fechamento = inicio.replace(

        hour=18,

        minute=0

    )



    if inicio < abertura or fim > fechamento:

        return jsonify({

            "mensagem":
            "Fora do horário de atendimento"

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

            ag["id"]

            for ag in lista

        ) + 1



    dados["id"] = novo_id

    dados["duracao"] = duracao



    lista.append(dados)


    salvar(lista)



    mensagem = f"""
💈 Novo agendamento Barbearia Regys

👤 Cliente: {dados['nome']}
✂️ Serviço: {dados['servico']}
📅 Data: {dados['data']}
🕒 Horário: {dados['hora']}
⏱️ Duração: {duracao} minutos
"""


    enviar_whatsapp(mensagem)



    return jsonify({

        "mensagem":
        "Agendamento realizado!"

    })





# ==========================
# CANCELAR AGENDAMENTO
# ==========================

@app.route("/cancelar/<int:id>", methods=["DELETE"])
def cancelar(id):


    if not session.get("barbeiro"):

        return jsonify({

            "mensagem":
            "Acesso negado"

        })



    lista = carregar()



    lista = [

        ag for ag in lista

        if ag["id"] != id

    ]



    salvar(lista)



    return jsonify({

        "mensagem":
        "Agendamento cancelado!"

    })





# ==========================
# EDITAR AGENDAMENTO
# ==========================

@app.route("/editar/<int:id>", methods=["PUT"])
def editar(id):


    if not session.get("barbeiro"):

        return jsonify({

            "mensagem":
            "Acesso negado"

        })



    dados = request.json


    lista = carregar()



    for ag in lista:

        if ag["id"] == id:

            ag["nome"] = dados.get(

                "nome",

                ag["nome"]

            )



    salvar(lista)



    return jsonify({

        "mensagem":
        "Agendamento editado!"

    })





# ==========================
# INICIAR SERVIDOR
# ==========================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(os.environ.get("PORT", 5001)),

        debug=False

    )
