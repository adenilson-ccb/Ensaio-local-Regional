import streamlit as st
from datetime import date
from io import BytesIO

import db

st.set_page_config(page_title="Ensaio Local", page_icon="🎵", layout="wide")

DIAS_SEMANA = [
    "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
    "Sexta-feira", "Sábado", "Domingo",
]

CORDAS = ["violino", "viola", "violoncelo"]
MADEIRAS = [
    "flauta", "clarinete", "clarone", "sax_soprano", "sax_alto", "sax_tenor",
    "sax_baritono", "oboe", "oboe_damore", "corne_ingles", "clarinete_alto",
]
METAIS = [
    "trompete", "trombone", "flugelhorn", "euphonium", "tuba",
    "trompete_cornet", "trompa", "trombonito", "baritono_pisto", "sax_horn",
]
MINISTERIO = [
    "anciaes", "diaconos", "coop_of_ministerial", "coop_jovens_menores",
    "enc_regionais", "enc_locais", "examinadoras",
]

LABELS = {
    "violino": "Violino", "viola": "Viola", "violoncelo": "Violoncelo",
    "flauta": "Flauta", "clarinete": "Clarinete", "clarone": "Clarone",
    "sax_soprano": "Sax Soprano", "sax_alto": "Sax Alto", "sax_tenor": "Sax Tenor",
    "sax_baritono": "Sax Barítono", "oboe": "Oboé", "oboe_damore": "Oboé D'Amore",
    "corne_ingles": "Corne Inglês", "clarinete_alto": "Clarinete Alto",
    "trompete": "Trompete", "trombone": "Trombone", "flugelhorn": "Flugelhorn",
    "euphonium": "Euphonium", "tuba": "Tuba", "trompete_cornet": "Trompete Cornet",
    "trompa": "Trompa", "trombonito": "Trombonito", "baritono_pisto": "Barítono pisto",
    "sax_horn": "Sax Horn",
    "anciaes": "Anciães", "diaconos": "Diáconos",
    "coop_of_ministerial": "Coop. do Of. Ministerial",
    "coop_jovens_menores": "Coop. de Jovens e Menores",
    "enc_regionais": "Enc. Regionais", "enc_locais": "Enc. Locais",
    "examinadoras": "Examinadoras",
}

META_CORDAS, META_MADEIRAS, META_METAIS = 0.50, 0.25, 0.25

DATA_PADRAO = date(2026, 9, 19)


# ---------------- Login com senha compartilhada ----------------

def checar_login():
    if st.session_state.get("autenticado"):
        return True

    st.title("🎵 Ensaio Local")
    senha = st.text_input("Senha de acesso", type="password")
    if st.button("Entrar"):
        if senha == st.secrets.get("APP_PASSWORD"):
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    return False


# ---------------- Geração de PDF do resumo ----------------

def gerar_pdf(contexto: dict) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Resumo do Ensaio", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Data: {contexto['data_str']} ({contexto['dia_semana']})", ln=True)
    pdf.cell(0, 8, f"Tipo: {contexto['tipo_ensaio']}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Encarregados", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for nome, localidade in contexto["encarregados"]:
        if nome or localidade:
            pdf.cell(0, 7, f"- {nome or '-'} / {localidade or '-'}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Resumo", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Quant. de Músicos: {contexto['total_musicos']}", ln=True)
    pdf.cell(0, 7, f"Quant. Organistas: {contexto['organistas']}", ln=True)
    pdf.cell(0, 7, f"Total: {contexto['total_musicos'] + contexto['organistas']}", ln=True)
    pdf.cell(0, 7, f"Total de Irmandade: {contexto['irmaos'] + contexto['irmas']}", ln=True)
    pdf.cell(0, 7, f"Total Geral (Músicos + Organistas + Irmandade): {contexto['total_geral']}", ln=True)
    pdf.ln(4)

    if contexto["hinos"]:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Hinos ensaiados", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for linha in contexto["hinos"].splitlines():
            pdf.multi_cell(0, 7, linha)

    return bytes(pdf.output())


# ---------------- Tela: Novo Registro ----------------

def tela_novo_registro():
    st.header("Novo Registro de Ensaio")

    tipo_ensaio = st.selectbox("Ensaio Local e Regional", ["Local", "Regional"], key="tipo_ensaio")

    data_ensaio = st.date_input(
        "Data do Ensaio",
        value=DATA_PADRAO,
        format="DD/MM/YYYY",
        key="data_ensaio",
    )
    dia_semana = DIAS_SEMANA[data_ensaio.weekday()]
    st.caption(f"Dia da semana: {dia_semana}")

    fora_padrao = dia_semana not in ("Quinta-feira", "Domingo", "Segunda-feira")
    if fora_padrao:
        st.info("Esse dia está fora do padrão habitual de ensaios — será marcado como tal.")

    st.subheader("Encarregados")
    st.caption("Quem vai reger a localidade de cada um.")
    encarregados = []
    for i in range(1, 4):
        col_a, col_b = st.columns(2)
        nome = col_a.text_input(f"Nome {i} — Nome do encarregado", key=f"nome_encarregado_{i}")
        localidade = col_b.text_input(f"Localidade {i} — Localidade", key=f"localidade_{i}")
        encarregados.append((nome, localidade))

    st.subheader("Músicos")

    with st.expander("Cordas", expanded=False):
        valores_cordas = {}
        cols = st.columns(len(CORDAS))
        for i, campo in enumerate(CORDAS):
            valores_cordas[campo] = cols[i].number_input(LABELS[campo], min_value=0, step=1, key=campo)
        total_cordas = sum(valores_cordas.values())
        st.caption(f"Total cordas: {total_cordas}")

    with st.expander("Madeiras", expanded=False):
        valores_madeiras = {}
        cols = st.columns(4)
        for i, campo in enumerate(MADEIRAS):
            valores_madeiras[campo] = cols[i % 4].number_input(LABELS[campo], min_value=0, step=1, key=campo)
        total_madeiras = sum(valores_madeiras.values())
        st.caption(f"Total madeiras: {total_madeiras}")

    with st.expander("Metais", expanded=False):
        valores_metais = {}
        cols = st.columns(4)
        for i, campo in enumerate(METAIS):
            valores_metais[campo] = cols[i % 4].number_input(LABELS[campo], min_value=0, step=1, key=campo)
        total_metais = sum(valores_metais.values())
        st.caption(f"Total metais: {total_metais}")

    with st.expander("Harmônico", expanded=False):
        acordeon = st.number_input("Harmônico (Acordeon)", min_value=0, step=1, key="acordeon")
        st.caption(f"Total harmônico: {acordeon}")

    organistas = st.number_input("Organistas", min_value=0, step=1, key="organistas")

    total_musicos = total_cordas + total_madeiras + total_metais + acordeon

    st.subheader("Ministério")
    st.caption("Não entra na soma de Total Geral — fica só para conferência.")
    valores_ministerio = {}
    cols = st.columns(4)
    for i, campo in enumerate(MINISTERIO):
        valores_ministerio[campo] = cols[i % 4].number_input(LABELS[campo], min_value=0, step=1, key=campo)
    total_ministerio = sum(valores_ministerio.values())
    st.caption(f"Total Ministério: {total_ministerio}")

    st.subheader("Irmandade")
    col1, col2 = st.columns(2)
    irmaos = col1.number_input("Irmãos", min_value=0, step=1, key="irmaos")
    irmas = col2.number_input("Irmãs", min_value=0, step=1, key="irmas")
    st.caption(f"Total de Irmandade: {irmaos + irmas}")

    st.subheader("Composição dos participantes")
    st.caption("Referência sugerida pela CCB: 50% Cordas, 25% Madeiras, 25% Metais.")
    c1, c2, c3 = st.columns(3)
    pc_cordas = (total_cordas / total_musicos) if total_musicos else 0
    pc_madeiras = (total_madeiras / total_musicos) if total_musicos else 0
    pc_metais = (total_metais / total_musicos) if total_musicos else 0
    c1.metric("Cordas", f"{pc_cordas:.0%}", help=f"meta: {META_CORDAS:.0%}")
    c2.metric("Madeiras", f"{pc_madeiras:.0%}", help=f"meta: {META_MADEIRAS:.0%}")
    c3.metric("Metais", f"{pc_metais:.0%}", help=f"meta: {META_METAIS:.0%}")

    visitantes = st.number_input("Visitantes", min_value=0, step=1, key="visitantes")

    hinos = st.text_area("Hinos ensaiados", placeholder="Ex: Hino 10 - ...\nHino 25 - ...", key="hinos")

    st.subheader("Resumo")
    r1, r2, r3 = st.columns(3)
    r1.metric("Quant. de Músicos", total_musicos)
    r2.metric("Quant. Organistas", organistas)
    r3.metric("Total", total_musicos + organistas)

    total_geral = total_musicos + organistas + irmaos + irmas
    st.metric("Total Geral (Músicos + Organistas + Irmandade)", total_geral)
    st.caption("O Ministério não entra nessa soma — fica só para conferência.")

    dados = {
        "data": data_ensaio.isoformat(),
        "dia_semana": dia_semana,
        "tipo_ensaio": tipo_ensaio,
        "nome_encarregado_1": encarregados[0][0], "localidade_1": encarregados[0][1],
        "nome_encarregado_2": encarregados[1][0], "localidade_2": encarregados[1][1],
        "nome_encarregado_3": encarregados[2][0], "localidade_3": encarregados[2][1],
        "fora_do_padrao": 1 if fora_padrao else 0,
        "irmaos": irmaos,
        "irmas": irmas,
        **valores_cordas,
        **valores_madeiras,
        **valores_metais,
        "acordeon": acordeon,
        "organistas": organistas,
        **valores_ministerio,
        "visitantes": visitantes,
        "hinos_ensaiados": hinos,
    }

    b1, b2 = st.columns(2)
    if b1.button("Salvar Ensaio", type="primary", use_container_width=True):
        db.salvar_culto(dados, [])
        st.success("Registro salvo com sucesso!")
        st.rerun()

    pdf_bytes = gerar_pdf({
        "data_str": data_ensaio.strftime("%d/%m/%Y"),
        "dia_semana": dia_semana,
        "tipo_ensaio": tipo_ensaio,
        "encarregados": encarregados,
        "total_musicos": total_musicos,
        "organistas": organistas,
        "irmaos": irmaos,
        "irmas": irmas,
        "total_geral": total_geral,
        "hinos": hinos,
    })
    b2.download_button(
        "Salvar em PDF",
        data=pdf_bytes,
        file_name=f"ensaio_{data_ensaio.isoformat()}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


# ---------------- Tela: Histórico ----------------

def tela_historico():
    st.header("Histórico de Ensaios")
    mostrar_fora_padrao = st.checkbox("Mostrar também datas fora do padrão", value=True)

    cultos = db.listar_cultos(limite=50)
    if not mostrar_fora_padrao:
        cultos = [c for c in cultos if not c.get("fora_do_padrao")]

    if not cultos:
        st.info("Nenhum registro ainda.")
        return

    for c in cultos:
        total_musicos = sum(c.get(campo, 0) or 0 for campo in CORDAS + MADEIRAS + METAIS) + (c.get("acordeon") or 0)
        tipo = c.get("tipo_ensaio") or ""
        titulo = f"{c['dia_semana']} — {c['data']}"
        if tipo:
            titulo += f" · {tipo}"
        titulo += f" · {total_musicos + (c.get('organistas') or 0)} presente(s) · {c.get('visitantes') or 0} visitante(s)"
        with st.expander(titulo):
            for i in range(1, 4):
                nome = c.get(f"nome_encarregado_{i}")
                localidade = c.get(f"localidade_{i}")
                if nome or localidade:
                    st.write(f"**Encarregado {i}:** {nome or '-'} · **Localidade:** {localidade or '-'}")
            st.write(f"**Irmãos:** {c.get('irmaos')} · **Irmãs:** {c.get('irmas')}")
            st.write(f"**Músicos:** {total_musicos} · **Organistas:** {c.get('organistas')}")
            if c.get("hinos_ensaiados"):
                st.write("**Hinos ensaiados:**")
                st.text(c["hinos_ensaiados"])


# ---------------- Main ----------------

def main():
    if not checar_login():
        return

    db.init_db()

    aba1, aba2 = st.tabs(["📝 Novo Registro", "📜 Histórico"])
    with aba1:
        tela_novo_registro()
    with aba2:
        tela_historico()


if __name__ == "__main__":
    main()
