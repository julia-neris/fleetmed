
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.utils import secure_filename
import pandas as pd
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = "troque-esta-chave-em-producao"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DATA_DIR = os.path.join(BASE_DIR, "data")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

MEDICOES_FILE = os.path.join(DATA_DIR, "medicoes.csv")
CONTRATOS_FILE = os.path.join(DATA_DIR, "contratos.csv")
FORNECEDORES_FILE = os.path.join(DATA_DIR, "fornecedores.csv")
USUARIOS_FILE = os.path.join(DATA_DIR, "usuarios.csv")

COLUNAS_MEDICAO = [
    "ID", "FornecedorUsuario", "CNPJ", "RazaoSocial", "Unidade", "Placa",
    "TipoCobranca", "Valor", "Competencia", "Descricao", "StatusSistema",
    "ErroSistema", "ValidacaoUnidade", "JustificativaUnidade",
    "DataUpload", "DataValidacao"
]

COLUNAS_UPLOAD = [
    "CNPJ", "RazaoSocial", "Unidade", "Placa", "TipoCobranca",
    "Valor", "Competencia", "Descricao"
]

def inicializar_bases():
    if not os.path.exists(USUARIOS_FILE):
        usuarios = pd.DataFrame([
            {"usuario": "admin", "senha": "admin123", "perfil": "admin", "unidade": "", "fornecedor": ""},
            {"usuario": "fornecedor1", "senha": "forn123", "perfil": "fornecedor", "unidade": "", "fornecedor": "Fornecedor Modelo"},
            {"usuario": "unidade1", "senha": "uni123", "perfil": "unidade", "unidade": "UNIDADE MODELO", "fornecedor": ""},
            {"usuario": "lve", "senha": "lve123", "perfil": "lve", "unidade": "", "fornecedor": ""}
        ])
        usuarios.to_csv(USUARIOS_FILE, index=False, encoding="utf-8-sig")

    if not os.path.exists(FORNECEDORES_FILE):
        fornecedores = pd.DataFrame([
            {
                "FornecedorUsuario": "fornecedor1",
                "FornecedorNome": "Fornecedor Modelo",
                "CNPJ": "00000000000100",
                "RazaoSocial": "FORNECEDOR MODELO LTDA"
            }
        ])
        fornecedores.to_csv(FORNECEDORES_FILE, index=False, encoding="utf-8-sig")

    if not os.path.exists(CONTRATOS_FILE):
        contratos = pd.DataFrame([
            {
                "CNPJ": "00000000000100",
                "RazaoSocial": "FORNECEDOR MODELO LTDA",
                "Unidade": "UNIDADE MODELO",
                "Placa": "ABC1D23",
                "TipoCobranca": "ARRENDAMENTO",
                "ValorContrato": 3500.00
            },
            {
                "CNPJ": "00000000000100",
                "RazaoSocial": "FORNECEDOR MODELO LTDA",
                "Unidade": "UNIDADE MODELO",
                "Placa": "XYZ9A88",
                "TipoCobranca": "MANUTENCAO",
                "ValorContrato": 0
            }
        ])
        contratos.to_csv(CONTRATOS_FILE, index=False, encoding="utf-8-sig")

    if not os.path.exists(MEDICOES_FILE):
        pd.DataFrame(columns=COLUNAS_MEDICAO).to_csv(MEDICOES_FILE, index=False, encoding="utf-8-sig")

def carregar_csv(caminho, colunas=None):
    if not os.path.exists(caminho):
        return pd.DataFrame(columns=colunas or [])
    return pd.read_csv(caminho, dtype=str).fillna("")

def salvar_csv(df, caminho):
    df.to_csv(caminho, index=False, encoding="utf-8-sig")

def usuario_logado():
    return session.get("usuario")

def perfil_logado():
    return session.get("perfil")

def normalizar_texto(valor):
    return str(valor).strip().upper()

def limpar_cnpj(valor):
    return "".join([c for c in str(valor) if c.isdigit()])

def valor_float(valor):
    try:
        if isinstance(valor, str):
            valor = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(valor)
    except:
        return None

def validar_linha(row, fornecedor_usuario):
    erros = []

    fornecedores = carregar_csv(FORNECEDORES_FILE)
    contratos = carregar_csv(CONTRATOS_FILE)

    cnpj = limpar_cnpj(row.get("CNPJ", ""))
    razao = normalizar_texto(row.get("RazaoSocial", ""))
    unidade = normalizar_texto(row.get("Unidade", ""))
    placa = normalizar_texto(row.get("Placa", ""))
    tipo = normalizar_texto(row.get("TipoCobranca", ""))
    valor = valor_float(row.get("Valor", ""))

    if not cnpj:
        erros.append("CNPJ obrigatório.")
    if not razao:
        erros.append("Razão social obrigatória.")
    if not unidade:
        erros.append("Unidade obrigatória.")
    if not placa:
        erros.append("Placa obrigatória.")
    if not tipo:
        erros.append("Tipo de cobrança obrigatório.")
    if valor is None:
        erros.append("Valor inválido ou obrigatório.")

    fornecedor_base = fornecedores[fornecedores["FornecedorUsuario"] == fornecedor_usuario]

    if fornecedor_base.empty:
        erros.append("Fornecedor não cadastrado na base.")
    else:
        cnpj_base = limpar_cnpj(fornecedor_base.iloc[0]["CNPJ"])
        razao_base = normalizar_texto(fornecedor_base.iloc[0]["RazaoSocial"])

        if cnpj and cnpj != cnpj_base:
            erros.append("CNPJ diferente do fornecedor logado.")

        if razao and razao != razao_base:
            erros.append("Razão social diferente do fornecedor logado.")

    contrato_match = contratos[
        (contratos["CNPJ"].apply(limpar_cnpj) == cnpj) &
        (contratos["RazaoSocial"].apply(normalizar_texto) == razao) &
        (contratos["Unidade"].apply(normalizar_texto) == unidade) &
        (contratos["Placa"].apply(normalizar_texto) == placa) &
        (contratos["TipoCobranca"].apply(normalizar_texto) == tipo)
    ]

    if contrato_match.empty:
        erros.append("Combinação CNPJ/Razão/Unidade/Placa/Tipo não encontrada na base contratual.")
    else:
        if tipo == "ARRENDAMENTO" and valor is not None:
            valor_contrato = valor_float(contrato_match.iloc[0]["ValorContrato"])
            if valor_contrato is not None and round(valor, 2) != round(valor_contrato, 2):
                erros.append(f"Valor de arrendamento divergente do contrato. Contrato: R$ {valor_contrato:,.2f}")

    if erros:
        return "BLOQUEADO", " | ".join(erros)

    return "OK", ""

@app.route("/")
def index():
    if not usuario_logado():
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()

        usuarios = carregar_csv(USUARIOS_FILE)
        match = usuarios[(usuarios["usuario"] == usuario) & (usuarios["senha"] == senha)]

        if not match.empty:
            session["usuario"] = usuario
            session["perfil"] = match.iloc[0]["perfil"]
            session["unidade"] = match.iloc[0].get("unidade", "")
            session["fornecedor"] = match.iloc[0].get("fornecedor", "")
            return redirect(url_for("dashboard"))

        flash("Usuário ou senha inválidos.", "erro")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not usuario_logado():
        return redirect(url_for("login"))

    medicoes = carregar_csv(MEDICOES_FILE, COLUNAS_MEDICAO)

    if perfil_logado() == "fornecedor":
        medicoes = medicoes[medicoes["FornecedorUsuario"] == usuario_logado()]
    elif perfil_logado() == "unidade":
        unidade = normalizar_texto(session.get("unidade", ""))
        medicoes = medicoes[medicoes["Unidade"].apply(normalizar_texto) == unidade]

    def soma_valor(df):
        total = 0
        for v in df.get("Valor", []):
            vf = valor_float(v)
            if vf:
                total += vf
        return total

    total_enviado = soma_valor(medicoes)
    aceito = soma_valor(medicoes[medicoes["ValidacaoUnidade"] == "SIM"])
    recusado = soma_valor(medicoes[medicoes["ValidacaoUnidade"] == "NAO"])
    pendente = soma_valor(medicoes[(medicoes["ValidacaoUnidade"] == "") & (medicoes["StatusSistema"] == "OK")])
    bloqueado = len(medicoes[medicoes["StatusSistema"] == "BLOQUEADO"])

    indicadores = {
        "linhas": len(medicoes),
        "total_enviado": total_enviado,
        "aceito": aceito,
        "recusado": recusado,
        "pendente": pendente,
        "bloqueado": bloqueado
    }

    return render_template("dashboard.html", indicadores=indicadores, perfil=perfil_logado())

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if not usuario_logado():
        return redirect(url_for("login"))

    if perfil_logado() not in ["fornecedor", "admin", "lve"]:
        flash("Seu perfil não tem permissão para upload.", "erro")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        arquivo = request.files.get("arquivo")
        if not arquivo:
            flash("Selecione um arquivo Excel.", "erro")
            return redirect(url_for("upload"))

        nome = secure_filename(arquivo.filename)
        caminho = os.path.join(UPLOAD_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{nome}")
        arquivo.save(caminho)

        try:
            df = pd.read_excel(caminho, dtype=str).fillna("")
        except Exception as e:
            flash(f"Erro ao ler o arquivo: {e}", "erro")
            return redirect(url_for("upload"))

        faltantes = [c for c in COLUNAS_UPLOAD if c not in df.columns]
        if faltantes:
            flash(f"Colunas ausentes na planilha: {', '.join(faltantes)}", "erro")
            return redirect(url_for("upload"))

        medicoes = carregar_csv(MEDICOES_FILE, COLUNAS_MEDICAO)
        novas_linhas = []

        fornecedor_usuario = usuario_logado()

        for _, row in df.iterrows():
            status, erro = validar_linha(row, fornecedor_usuario)
            valor = valor_float(row.get("Valor", ""))
            nova = {
                "ID": str(uuid.uuid4()),
                "FornecedorUsuario": fornecedor_usuario,
                "CNPJ": limpar_cnpj(row.get("CNPJ", "")),
                "RazaoSocial": normalizar_texto(row.get("RazaoSocial", "")),
                "Unidade": normalizar_texto(row.get("Unidade", "")),
                "Placa": normalizar_texto(row.get("Placa", "")),
                "TipoCobranca": normalizar_texto(row.get("TipoCobranca", "")),
                "Valor": valor if valor is not None else row.get("Valor", ""),
                "Competencia": str(row.get("Competencia", "")).strip(),
                "Descricao": str(row.get("Descricao", "")).strip(),
                "StatusSistema": status,
                "ErroSistema": erro,
                "ValidacaoUnidade": "",
                "JustificativaUnidade": "",
                "DataUpload": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "DataValidacao": ""
            }
            novas_linhas.append(nova)

        medicoes = pd.concat([medicoes, pd.DataFrame(novas_linhas)], ignore_index=True)
        salvar_csv(medicoes, MEDICOES_FILE)

        ok = len([x for x in novas_linhas if x["StatusSistema"] == "OK"])
        bloq = len([x for x in novas_linhas if x["StatusSistema"] == "BLOQUEADO"])

        flash(f"Upload realizado. Linhas OK: {ok}. Linhas bloqueadas: {bloq}.", "sucesso")
        return redirect(url_for("medicoes"))

    return render_template("upload.html")

@app.route("/medicoes")
def medicoes():
    if not usuario_logado():
        return redirect(url_for("login"))

    df = carregar_csv(MEDICOES_FILE, COLUNAS_MEDICAO)

    if perfil_logado() == "fornecedor":
        df = df[df["FornecedorUsuario"] == usuario_logado()]
    elif perfil_logado() == "unidade":
        unidade = normalizar_texto(session.get("unidade", ""))
        df = df[df["Unidade"].apply(normalizar_texto) == unidade]

    registros = df.to_dict(orient="records")
    return render_template("medicoes.html", registros=registros, perfil=perfil_logado())

@app.route("/validar/<id>", methods=["POST"])
def validar(id):
    if not usuario_logado():
        return redirect(url_for("login"))

    if perfil_logado() not in ["unidade", "admin", "lve"]:
        flash("Seu perfil não tem permissão para validar.", "erro")
        return redirect(url_for("medicoes"))

    validacao = request.form.get("validacao", "")
    justificativa = request.form.get("justificativa", "").strip()

    if validacao == "NAO" and not justificativa:
        flash("Quando a validação for NÃO, a justificativa é obrigatória.", "erro")
        return redirect(url_for("medicoes"))

    df = carregar_csv(MEDICOES_FILE, COLUNAS_MEDICAO)
    idx = df.index[df["ID"] == id].tolist()

    if not idx:
        flash("Medição não encontrada.", "erro")
        return redirect(url_for("medicoes"))

    i = idx[0]
    if df.loc[i, "StatusSistema"] != "OK":
        flash("Essa linha está bloqueada pelo sistema e não pode ser validada.", "erro")
        return redirect(url_for("medicoes"))

    df.loc[i, "ValidacaoUnidade"] = validacao
    df.loc[i, "JustificativaUnidade"] = justificativa
    df.loc[i, "DataValidacao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    salvar_csv(df, MEDICOES_FILE)

    if validacao == "NAO":
        print(f"[EMAIL AUTOMÁTICO SIMULADO] Enviar negativa ao fornecedor da linha {id}: {justificativa}")

    flash("Validação salva com sucesso.", "sucesso")
    return redirect(url_for("medicoes"))

@app.route("/exportar")
def exportar():
    if not usuario_logado():
        return redirect(url_for("login"))

    if perfil_logado() not in ["admin", "lve"]:
        flash("Seu perfil não tem permissão para exportar.", "erro")
        return redirect(url_for("dashboard"))

    df = carregar_csv(MEDICOES_FILE, COLUNAS_MEDICAO)
    caminho = os.path.join(EXPORT_DIR, f"medicoes_consolidadas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    df.to_excel(caminho, index=False)
    return send_file(caminho, as_attachment=True)

@app.route("/modelo")
def modelo():
    dados = pd.DataFrame([
        {
            "CNPJ": "00000000000100",
            "RazaoSocial": "FORNECEDOR MODELO LTDA",
            "Unidade": "UNIDADE MODELO",
            "Placa": "ABC1D23",
            "TipoCobranca": "ARRENDAMENTO",
            "Valor": 3500.00,
            "Competencia": "04/2026",
            "Descricao": "Arrendamento mensal"
        },
        {
            "CNPJ": "00000000000100",
            "RazaoSocial": "FORNECEDOR MODELO LTDA",
            "Unidade": "UNIDADE MODELO",
            "Placa": "XYZ9A88",
            "TipoCobranca": "MANUTENCAO",
            "Valor": 780.50,
            "Competencia": "04/2026",
            "Descricao": "Manutenção preventiva"
        }
    ])
    caminho = os.path.join(EXPORT_DIR, "modelo_upload_medicao.xlsx")
    dados.to_excel(caminho, index=False)
    return send_file(caminho, as_attachment=True)

if __name__ == "__main__":
    inicializar_bases()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
